#ifndef DeepInc_SERVER_SERVER_H
#define DeepInc_SERVER_SERVER_H

#include "ps/ps.h"
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <set>
#include <unistd.h>
#include "../common/cpu_reducer.h"
#include "msg.h"

#define SERVER_KEY_TYPE uint64_t
#define SERVER_DATA_TYPE char
#define DEBUG_PRINT_TENSOR_VALUE(X) (*((float *)(X) + 0))
#define DEBUG_PRINT_TENSOR_ADDRESS(X) (reinterpret_cast<uint64_t>(X))

namespace deep_inc
{
    namespace server
    {

        struct UpdateBuf
        {
            std::vector<ps::KVMeta> request;
            BytePSArray merged;
        };

        volatile bool log_key_info_ = false;
        volatile bool is_server_ = true;
        ps::Node::Role role_;
        int preferred_rank = -1;
        volatile bool sync_mode_ = true;
        size_t engine_thread_num_ = 4;
        volatile bool enable_schedule_ = false;

        std::mutex pullresp_mu_;
        std::unordered_map<uint64_t, ps::KVPairs<char>> push_response_map_;
        std::unordered_map<uint64_t, ps::KVPairs<char>> pull_response_map_;

        // byteps handler
        std::mutex handle_mu_;
        std::mutex update_buf_mu_;
        std::unordered_map<uint64_t, UpdateBuf> update_buf_;
        // std::unordered_map<uint64_t, std::unique_ptr<common::compressor::Compressor>> compressor_map_;

        // push & pull flag
        std::vector<std::mutex> flag_mu_;
        std::vector<std::unordered_map<uint64_t, bool>> is_push_finished_;
        std::vector<std::unordered_map<uint64_t, std::vector<ps::KVMeta>>> q_pull_reqmeta_;
        std::vector<std::unordered_map<uint64_t, std::set<int>>> seen_sender_;
        std::vector<std::unordered_map<uint64_t, size_t>> pull_cnt_;

        deep_inc::common::CpuReducer *inc_reducer_;
        ps::KVServer<SERVER_DATA_TYPE> *inc_server_;
        std::unordered_map<uint64_t, BytePSArray> store_;

        std::vector<uint64_t> acc_load_;

        int DivUp(int x, int y) { return (x + y - 1) / y; }
        int RoundUp(int x, int y) { return DivUp(x, y) * y; }

        uint64_t DecodeKey(ps::Key key)
        {
            auto kr = ps::Postoffice::Get()->GetServerKeyRanges()[ps::MyRank()];
            return key - kr.begin();
        }

        uint64_t EncodeKey(ps::Key key)
        {
            auto kr = ps::Postoffice::Get()->GetServerKeyRanges()[ps::MyRank()];
            return key + kr.begin();
        }

        extern "C" void start_server();
    }
}

#endif // DeepInc_SERVER_SERVER_H
