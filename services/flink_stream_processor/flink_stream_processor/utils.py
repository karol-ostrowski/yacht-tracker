from pyflink.datastream import OutputTag
from pyflink.common.typeinfo import Types

LATE_DATA_TAG = OutputTag(
    tag_id="late_data",
    type_info=Types.ROW_NAMED(
        ["id", "x", "y", "timestamp"],
        [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE()]
    )
)