import dayjs from 'dayjs';

/**
 * Format a timestamp into a human-readable group time string.
 * @param timestamp - The timestamp to format (string, number, or Date)
 * @returns Formatted time string (e.g., "HH:mm", "昨天 HH:mm", "MM-DD HH:mm")
 */
export const formatGroupTime = (timestamp: string | number | Date | dayjs.Dayjs): string => {
  const dayjsObj = dayjs(timestamp);
  return dayjsObj.format('YYYY-MM-DD HH:mm');
};
