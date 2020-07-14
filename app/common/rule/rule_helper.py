import numpy as np
from .math_utils import MathUtils
from datetime import datetime, time
import pytz
class ZoneHelper:

    @staticmethod
    def is_zone_valid(zone):
        if len(zone) > 2:
            for point in zone:
                if all(isinstance(x, float) and x <= 1 for x in point) is True:
                    return True
        return False

    @staticmethod
    def is_match_zone_contition(condition, obj):
        condition = np.array(condition)
        zonerule = condition.astype(np.float)
        if ZoneHelper.is_zone_valid(zonerule) is False:
            return False

        point = MathUtils.tranform_bbox_to_point(obj["bbox"])
        point_in_zone = MathUtils.is_point_in_polygon(point, zonerule)
        if point_in_zone is True:
            return True

        return False
class TimeHelper:

    @staticmethod
    def is_time_in_time_range(time_range, comparing_time):
        """
        """
        # print(type(comparing_time))
        if not isinstance(comparing_time, (int, float)):
            raise RuntimeError(
                '"comparing_time" Required an integer or float value')

        if isinstance(time_range, list) and len(time_range) == 2:
            starttime_str = time_range[0]
            endtime_str = time_range[1]

            starttime_hour = int(starttime_str.split(":")[0])
            starttime_minute = int(starttime_str.split(":")[1])
            starttime_second = int(starttime_str.split(":")[2])
            starttime = time(starttime_hour, starttime_minute,
                             starttime_second)

            endtime_hour = int(endtime_str.split(":")[0])
            endtime_minute = int(endtime_str.split(":")[1])
            endtime_second = int(endtime_str.split(":")[2])
            endtime = time(endtime_hour, endtime_minute, endtime_second)

            dt = datetime.fromtimestamp(
                comparing_time, pytz.timezone("Asia/Saigon"))
            dt_time = dt.time()
            # dt_time = dt.weekday()

            if starttime < endtime:
                # in day time
                return starttime <= dt_time <= endtime
            else:
                # midnight time
                return dt_time >= starttime or dt_time <= endtime

        return False
    @staticmethod
    def is_match_time_condition(condition, comparing_time):
        """
        """
        is_matches = []
        for time_range in condition:

            is_matches.append(TimeHelper.is_time_in_time_range(
                time_range, comparing_time))

        return True if True in is_matches else False