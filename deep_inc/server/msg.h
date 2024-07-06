
#ifndef DeepInc_SERVER_MSG_H
#define DeepInc_SERVER_MSG_H
#include "ps/ps.h"

namespace deep_inc
{
    namespace server
    {
        enum class RequestType
        {
            kDefaultPushPull,
            kRowSparsePushPull,
            kCompressedPushPull
        };

        enum BytePSEngineOperation
        {
            SUM_RECV,
            COPY_FIRST,
            ALL_RECV,
            TERMINATE
        };

        struct DataHandleType
        {
            RequestType requestType;
            int dtype;
        };

        struct BytePSEngineMessage
        {
            uint64_t id;
            DataHandleType type;
            uint64_t key;
            void *dst;
            void *src;
            size_t len;
            BytePSEngineOperation ops;
            ps::KVPairs<char> sarray; // to temporarily hold it and auto release
            ps::KVMeta req_meta;
        };

        struct BytePSArray
        {
            char *tensor;
            size_t len;
            int dtype;
            ps::KVPairs<char> tmp_sarray;
        };
    }
}

#endif // DeepInc_SERVER_MSG_H