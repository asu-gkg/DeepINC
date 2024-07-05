#include "cpu_reducer.h"

namespace deep_inc
{
    namespace common
    {
        CpuReducer::CpuReducer(std::shared_ptr<DeepIncComm> comm)
        {
            comm_ = comm;
            std::cout << "CpuReducer created" << std::endl;
        }
    }
}