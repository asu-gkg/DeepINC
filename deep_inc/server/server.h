#ifndef SERVER_H
#define SERVER_H

#include "ps/ps.h"
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <set>
#include <unistd.h>

namespace deep_inc {
    namespace server {
        volatile bool log_key_info_ = false;

        extern "C" void start_server();
    }
}

#endif  // SERVER_H
