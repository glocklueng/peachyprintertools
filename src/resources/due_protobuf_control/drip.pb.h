/* Automatically generated nanopb header */
/* Generated by nanopb-0.3.1 at Tue Jan 27 15:25:19 2015. */

#ifndef PB_DRIP_PB_H_INCLUDED
#define PB_DRIP_PB_H_INCLUDED
#include <pb.h>

#if PB_PROTO_HEADER_VERSION != 30
#error Regenerate this file with the current version of nanopb generator.
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Enum definitions */
/* Struct definitions */
typedef struct _DripRecorded {
    int32_t id;
    int32_t drips;
} DripRecorded;

/* Default values for struct fields */

/* Initializer values for message structs */
#define DripRecorded_init_default                {0, 0}
#define DripRecorded_init_zero                   {0, 0}

/* Field tags (for use in manual encoding/decoding) */
#define DripRecorded_id_tag                      1
#define DripRecorded_drips_tag                   2

/* Struct field encoding specification for nanopb */
extern const pb_field_t DripRecorded_fields[3];

/* Maximum encoded size of messages (where known) */
#define DripRecorded_size                        22

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif
