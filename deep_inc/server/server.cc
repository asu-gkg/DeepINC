#include "server.h"
#include <iostream>

namespace deep_inc{
    namespace server{
        extern "C" void start_server(){
            std::cout << "Server started" << std::endl;
        }
    }
}