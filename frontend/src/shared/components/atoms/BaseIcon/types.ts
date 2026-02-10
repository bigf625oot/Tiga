export interface IBaseIconProps {
  /**
   * Icon name from Iconify (e.g., 'mdi:home')
   */
  icon: string;
  
  /**
   * Size of the icon. Can be a number (pixels) or string (e.g. '2em', '24px').
   * Default: 24
   */
  size?: string | number;
  
  /**
   * Icon color. Can be any CSS color string.
   */
  color?: string;
  
  /**
   * Rotation in degrees (0, 90, 180, 270)
   */
  rotate?: number | string;
  
  /**
   * Horizontal or Vertical flip ('horizontal', 'vertical', 'horizontal,vertical')
   */
  flip?: string;
  
  /**
   * Toggles inline mode (adds vertical-align: -0.125em)
   */
  inline?: boolean;
  
  /**
   * Fallback icon to show if the main icon fails to load
   */
  fallback?: string;
  
  /**
   * Aria label for accessibility
   */
  ariaLabel?: string;
  
  /**
   * Custom class
   */
  class?: string;

  /**
   * Whether to spin the icon (adds animate-spin class)
   */
  spin?: boolean;
}
