#ifndef DeepInc_COMMON_CPU_REDUCER_H
#define DeepInc_COMMON_CPU_REDUCER_H

#include <stdint.h>
#include <cstring>
#include <memory>
#include <iostream>

typedef void DeepIncComm;

namespace deep_inc
{
    namespace common
    {
        class CpuReducer
        {
        public:
            CpuReducer(std::shared_ptr<DeepIncComm> comm);
            ~CpuReducer()
            {
                std::cout << "Clear CpuReducer" << std::endl;
            };

        private:
            std::shared_ptr<DeepIncComm> comm_;
        };

    }

}

#endif // DeepInc_COMMON_CPU_REDUCER_H