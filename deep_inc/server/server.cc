#include "server.h"
#include <iostream>

namespace deep_inc
{
    namespace server
    {

        void init_global_env()
        {
            // enable to print key profile
            log_key_info_ = ps::GetEnv("PS_KEY_LOG", 0);
            printf("log_key_info_ = %d\n", log_key_info_);
            // std::string role_str = GetEnv("DMLC_ROLE", "server");
            // role_ = ps::GetRole(role_str);
            // if (role_str == std::string("server"))
            // {
            //     is_server_ = true;
            //     preferred_rank = -1;
            // }
            // else
            // {
            //     is_server_ = false;
            //     preferred_rank = 0;
            // }

            // LOG(INFO) << "This is a " << role_str << " is_server=" << is_server_;

            // // enable engine block mode (default disabled)
            // is_engine_blocking_ = GetEnv("BYTEPS_SERVER_ENGINE_BLOCKING", 0);
            // if (is_engine_blocking_)
            //     LOG(INFO) << "Enable blocking mode of the server engine";

            // // sync or async training
            // sync_mode_ = !GetEnv("BYTEPS_ENABLE_ASYNC", 0);
            // if (!sync_mode_)
            //     LOG(INFO) << "BytePS server is enabled asynchronous training";

            // // debug mode
            // debug_mode_ = GetEnv("BYTEPS_SERVER_DEBUG", 0);
            // debug_key_ = GetEnv("BYTEPS_SERVER_DEBUG_KEY", 0);
            // if (debug_mode_)
            //     LOG(INFO) << "Debug mode enabled! Printing key " << debug_key_;

            // // number of engine thread
            // // invalid if is_engine_blocking = true
            // engine_thread_num_ = GetEnv("BYTEPS_SERVER_ENGINE_THREAD", 4);
            // LOG(INFO) << "BytePS server engine uses " << engine_thread_num_ << " threads"
            //           << ", consider increasing BYTEPS_SERVER_ENGINE_THREAD for higher "
            //              "performance";
            // CHECK_GE(engine_thread_num_, 1);

            // // enable scheduling for server engine
            // enable_schedule_ = GetEnv("BYTEPS_SERVER_ENABLE_SCHEDULE", 0);
            // if (enable_schedule_)
            //     LOG(INFO) << "Enable engine scheduling for BytePS server";
        }

        extern "C" void start_server()
        {
            init_global_env();
            std::cout << "Server started" << std::endl;
        }
    }
}