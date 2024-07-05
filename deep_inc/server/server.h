#ifndef DeepInc_SERVER_SERVER_H
#define DeepInc_SERVER_SERVER_H

#include "ps/ps.h"
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <set>
#include <unistd.h>
#include "../common/cpu_reducer.h"

namespace deep_inc
{
    namespace server
    {
        volatile bool log_key_info_ = false;
        volatile bool is_server_ = true;
        ps::Node::Role role_;
        int preferred_rank = -1;
        volatile bool sync_mode_ = true;
        size_t engine_thread_num_ = 4;
        volatile bool enable_schedule_ = false;
        deep_inc::common::CpuReducer *inc_reducer_;
        std::vector<uint64_t> acc_load_;
        extern "C" void start_server();
    }
}

#endif // DeepInc_SERVER_SERVER_H
