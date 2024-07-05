#include "server.h"
#include <iostream>
#include "queue.h"

namespace deep_inc
{
    namespace server
    {
        // engine related
        std::vector<PriorityQueue*> engine_queues_;
        std::vector<std::thread*> engine_threads_;
        void DeepIncServerEngineThread(int i)
        {
            std::cout << "DeepIncServer Engine Thread " << i << " started" << std::endl;
        }

        void init_global_env()
        {
            log_key_info_ = ps::GetEnv("PS_KEY_LOG", 0); // default 0
            printf("log_key_info_ = %d\n", log_key_info_);
            std::string role_str = ps::GetEnv("ROLE", "server"); // default "server"
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
            CHECK_GE(engine_thread_num_, 1);

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
            if(sync_mode_){
                for (size_t i = 0; i < engine_thread_num_; i++)
                {
                    engine_queues_.push_back(new PriorityQueue(enable_schedule_));
                    engine_threads_.push_back(new std::thread(DeepIncServerEngineThread, i));
                }
            }


        }
    }
}