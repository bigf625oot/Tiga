import dayjs from 'dayjs';

/**
 * Format a timestamp into a human-readable group time string.
 * @param timestamp - The timestamp to format (string, number, or Date)
 * @returns Formatted time string (e.g., "HH:mm", "昨天 HH:mm", "MM-DD HH:mm")
 */
export const formatGroupTime = (timestamp: string | number | Date | dayjs.Dayjs): string => {
  const dayjsObj = dayjs(timestamp);
  const now = dayjs();
  
  if (dayjsObj.isSame(now, 'day')) {
    return dayjsObj.format('HH:mm');
  } else if (dayjsObj.isSame(now.subtract(1, 'day'), 'day')) {
    return '昨天 ' + dayjsObj.format('HH:mm');
  } else {
    return dayjsObj.format('MM-DD HH:mm');
  }
};
