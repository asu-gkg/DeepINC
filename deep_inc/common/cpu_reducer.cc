#include "cpu_reducer.h"

namespace deep_inc
{
    namespace common
    {
        CpuReducer::CpuReducer(std::shared_ptr<DeepIncComm> comm)
        {
            comm_ = comm;
            std::cout << "CpuReducer created" << std::endl;

#ifndef BYTEPS_BUILDING_SERVER
            std::vector<int> peers;
            auto pcie_size = BytePSGlobal::GetPcieSwitchSize();
            for (int i = BytePSGlobal::GetLocalRank() % pcie_size;
                 i < BytePSGlobal::GetLocalSize(); i += pcie_size)
            {
                peers.push_back(i);
            }
            if (comm)
            {
                _comm = std::make_shared<BytePSCommSocket>(comm, std::string("cpu"), peers);
            }
            else
            {
                _comm = nullptr;
            }
#endif
            if (getenv("BYTEPS_OMP_THREAD_PER_GPU"))
            {
                _num_threads = atoi(getenv("BYTEPS_OMP_THREAD_PER_GPU"));
            }
            else
            {
                _num_threads = 4;
            }
        }

        int CpuReducer::copy(void *dst, const void *src, size_t len)
        {
            auto in = (float *)src;
            auto out = (float *)dst;
#pragma omp parallel for simd num_threads(_num_threads)
            for (size_t i = 0; i < len / 4; ++i)
            {
                out[i] = in[i];
            }
            if (len % 4)
            {
                std::memcpy(out + len / 4, in + len / 4, len % 4);
            }
            return 0;
        }
    }
}