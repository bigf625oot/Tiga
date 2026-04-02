declare module 'vue-virtual-scroller' {
  import type { VNodeProps, AllowedComponentProps, ComponentCustomProps } from 'vue';

  /**
   * 全局 Vue 组件的基础 Props
   * 包含 class, style, key, ref 等原生属性以及事件绑定
   */
  type GlobalProps = VNodeProps & AllowedComponentProps & ComponentCustomProps;

  /**
   * Scroller 通用事件契约
   */
  export interface ScrollerEmits {
    (e: 'resize'): void;
    (e: 'visible'): void;
    (e: 'hidden'): void;
    (e: 'update', startIndex: number, endIndex: number, visibleStartIndex: number, visibleEndIndex: number): void;
  }

  /**
   * --- RecycleScroller ---
   */
  export interface RecycleScrollerProps<T = any> {
    items: T[];
    itemSize: number | string;
    keyField?: string;
    direction?: 'vertical' | 'horizontal';
    buffer?: number;
    prerender?: number;
    emitUpdate?: boolean;
    updateInterval?: number;
    listClass?: string;
    itemClass?: string;
    listTag?: string;
    itemTag?: string;
  }

  export interface RecycleScrollerSlots<T = any> {
    default(props: { item: T; index: number; active: boolean }): any;
    before(): any;
    after(): any;
    empty(): any;
  }

  // 抛弃冗长的 DefineComponent，直接使用构造函数签名与结构化类型，
  // 完美契合 Volar (Vue Language Server) 的底层类型推导引擎。
  export declare const RecycleScroller: new <T = any>() => {
    $props: RecycleScrollerProps<T> & GlobalProps;
    $slots: RecycleScrollerSlots<T>;
    $emit: ScrollerEmits;
  };

  /**
   * --- DynamicScroller ---
   */
  export interface DynamicScrollerProps<T = any> extends Omit<RecycleScrollerProps<T>, 'itemSize'> {
    minItemSize: number | string;
  }

  export declare const DynamicScroller: new <T = any>() => {
    $props: DynamicScrollerProps<T> & GlobalProps;
    $slots: RecycleScrollerSlots<T>; 
    $emit: ScrollerEmits;
  };

  /**
   * --- DynamicScrollerItem ---
   */
  export interface DynamicScrollerItemProps<T = any> {
    item: T;
    active: boolean;
    sizeDependencies?: any[];
    watchData?: boolean;
    tag?: string;
    emitResize?: boolean;
  }

  export declare const DynamicScrollerItem: new <T = any>() => {
    $props: DynamicScrollerItemProps<T> & GlobalProps;
    $slots: { default(): any };
    $emit: (e: 'resize') => void;
  };
}
