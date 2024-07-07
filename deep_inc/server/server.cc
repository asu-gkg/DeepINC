#include "server.h"
#include <iostream>
#include "queue.h"

namespace deep_inc
{
    namespace server
    {
        // engine related
        std::vector<PriorityQueue *> engine_queues_;
        std::vector<std::thread *> engine_threads_;

        UpdateBuf *GetUpdateBuf(uint64_t key)
        {
            std::lock_guard<std::mutex> lock(update_buf_mu_);
            return &update_buf_[key];
        }

        void SendPullResponse(const DataHandleType type, const uint64_t key,
                              const ps::KVMeta &req_meta, ps::KVServer<char> *server)
        {
            std::lock_guard<std::mutex> lock(pullresp_mu_);
            auto updates = GetUpdateBuf(key);
            CHECK(updates->merged.tensor) << "init " << key << " first";
            char *data = updates->merged.tensor;
            auto len = updates->merged.len;

            // send pull response
            auto iterator = pull_response_map_.find(key);
            if (iterator == pull_response_map_.end())
            { // new key
                ps::KVPairs<char> response;
                response.keys = {EncodeKey(key)};
                response.lens = {len};
                response.vals = ps::SArray<char>(data, len, false); // zero copy
                pull_response_map_[key] = response;                 // add to the map
                server->Response(req_meta, response);
            }
            else
            { // not new key, then reuse the memory address to avoid ibv_reg_mr on
              // RDMA data path
                ps::KVPairs<char> *response = &iterator->second;

                auto p = static_cast<char *>(data);
                CHECK(p);
                response->lens = {len};
                response->vals = ps::SArray<char>(p, len, false);
                server->Response(req_meta, *response);
            }
        }

        void DeepIncServerEngineThread(int i)
        {
            auto &q = engine_queues_[i];
            while (true)
            {
                // BytePSEngineMessage msg;
                // q->WaitAndPop(&msg);
                // if (msg.ops == TERMINATE)
                //     break;
                // // do some check
                // CHECK(msg.dst);
                // CHECK(msg.src);

                // if (msg.ops == ALL_RECV)
                // {
                //     // 2. no compress
                //     auto updates = GetUpdateBuf(msg.key);
                //     updates->merged.tensor = reinterpret_cast<char *>(msg.src);
                //     updates->merged.len = msg.len;
                // }

                // switch (msg.ops)
                // {
                // case COPY_FIRST:
                // {
                //     inc_reducer_->copy(msg.dst, msg.src, msg.len);
                // }
                // break;

                // case ALL_RECV:
                // {
                //     std::lock_guard<std::mutex> lock(flag_mu_[i]);
                //     if (is_push_finished_[i].find(msg.key) == is_push_finished_[i].end())
                //     {
                //         is_push_finished_[i][msg.key] = false;
                //         pull_cnt_[i][msg.key] = 0;
                //         seen_sender_[i][msg.key].clear();
                //     }
                //     is_push_finished_[i][msg.key] = true;

                //     auto it = q_pull_reqmeta_[i][msg.key].begin();
                //     while (it != q_pull_reqmeta_[i][msg.key].end())
                //     {
                //         if (seen_sender_[i][msg.key].find(it->sender) ==
                //             seen_sender_[i][msg.key].end())
                //         {
                //             SendPullResponse(msg.type, msg.key, *it, inc_server_);
                //             pull_cnt_[i][msg.key] += 1;
                //             seen_sender_[i][msg.key].insert(it->sender);
                //             it = q_pull_reqmeta_[i][msg.key].erase(it);
                //         }
                //         else
                //         {
                //             ++it;
                //         }
                //         if (pull_cnt_[i][msg.key] == (size_t)ps::NumWorkers())
                //         {
                //             is_push_finished_[i][msg.key] = false;
                //             pull_cnt_[i][msg.key] = 0;
                //             seen_sender_[i][msg.key].clear();
                //             break;
                //         }
                //     }
                // }
                // break;

                // case SUM_RECV:
                // {
                //     auto bps_type = inc_reducer_->GetDataType(msg.type.dtype);
                //     CHECK_GE(inc_reducer_->sum(msg.dst, msg.src, msg.len, bps_type), 0);
                // }
                // break;
                // default:
                //     CHECK(0);
                // }
            }
        }

        void BytePSHandler(const ps::KVMeta &req_meta,
                           const ps::KVPairs<char> &req_data,
                           ps::KVServer<char> *server)
        {
        }

        void init_global_env()
        {
            log_key_info_ = ps::GetEnv("PS_KEY_LOG", 0); // default 0
            printf("log_key_info_ = %d\n", log_key_info_);
            std::string role_str = ps::GetEnv("DMLC_ROLE", "server"); // default "server"
            printf("role_str = %s\n", role_str.c_str());
            if (role_str == std::string("server"))
            {
                role_ = ps::Node::Role::SERVER;
                is_server_ = true;
                preferred_rank = -1;
            }
            else
            {
                is_server_ = false;
                preferred_rank = 0;
            }
            LOG(INFO) << "This is a " << role_str << " is_server=" << is_server_;
            // sync or async training
            sync_mode_ = !ps::GetEnv("ENABLE_ASYNC", 0);
            if (!sync_mode_)
            {
                LOG(INFO) << "DeepINC server is enabled asynchronous training";
            }

            // number of engine thread
            // invalid if is_engine_blocking = true
            engine_thread_num_ = ps::GetEnv("SERVER_ENGINE_THREAD", 4);
            LOG(INFO) << "DeepINC server engine uses " << engine_thread_num_ << " threads"
                      << ", consider increasing SERVER_ENGINE_THREAD for higher "
                         "performance";

            // enable scheduling for server engine
            enable_schedule_ = ps::GetEnv("SERVER_ENABLE_SCHEDULE", 0);
            if (enable_schedule_)
            {
                LOG(INFO) << "Enable engine scheduling for DeepINC server";
            }
        }

        extern "C" void start_server()
        {
            init_global_env();
            std::cout << "Server started" << std::endl;
            inc_reducer_ = new deep_inc::common::CpuReducer(nullptr);

            for (size_t i = 0; i < engine_thread_num_; i++)
            {
                acc_load_.push_back(0);
            }
            if (sync_mode_)
            {
                for (size_t i = 0; i < engine_thread_num_; i++)
                {
                    engine_queues_.push_back(new PriorityQueue(enable_schedule_));
                    engine_threads_.push_back(new std::thread(DeepIncServerEngineThread, i));
                }
            }
            // init server instance
            ps::Start(0, "byteps\0");
            inc_server_ = new ps::KVServer<SERVER_DATA_TYPE>(0);
            // inc_server_->set_request_handle(DeepIncServerHandle);

            if (!ps::Postoffice::Get()->is_recovery())
            {
                ps::Postoffice::Get()->Barrier(
                    0, ps::kWorkerGroup + ps::kServerGroup + ps::kScheduler);
            }

            // clean the server resource
            ps::Finalize(0, true);
            if (inc_server_)
            {
                delete inc_server_;
                inc_server_ = nullptr;
            }
            if (inc_reducer_)
            {
                delete inc_reducer_;
                inc_reducer_ = nullptr;
            }
            BytePSEngineMessage msg;
            msg.ops = TERMINATE;
            for (auto q : engine_queues_)
                q->Push(msg);
            for (auto t : engine_threads_)
                t->join();

            for (auto &it : store_)
            {
                if (it.second.tensor)
                {
                    free(it.second.tensor);
                }
            }

            LOG(INFO) << "BytePS server quited normally";
            return;
        }
    }
}
