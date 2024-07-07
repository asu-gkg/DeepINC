#ifndef DeepInc_COMMON_CPU_REDUCER_H
#define DeepInc_COMMON_CPU_REDUCER_H

#include <stdint.h>
#include <cstring>
#include <memory>
#include <iostream>
#include "global.h"

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
            int copy(void* dst, const void* src, size_t len);

        private:
            std::shared_ptr<DeepIncComm> comm_;
            int _num_threads;
        };

    }

}

#endif // DeepInc_COMMON_CPU_REDUCER_H