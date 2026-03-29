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

export const formatTime = (ts: any): string => {
  if (!ts) return '';
  return dayjs(ts).format('YYYY-MM-DD HH:mm');
};

export const formatDuration = (ms?: number): string => {
  if (!ms) return '';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m${Math.floor((ms % 60000) / 1000)}s`;
};

export const formatFileSize = (bytes?: number): string => {
  if (bytes == null) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};
