import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { defineComponent } from 'vue'
import PermissionConfig from '../PermissionConfig.vue'

vi.mock('@/components/ui/toast/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

vi.mock('@/components/ui/button', () => ({
  Button: { template: '<button v-bind="$attrs"><slot /></button>' },
}))
vi.mock('@/components/ui/card', () => ({
  Card: { template: '<div><slot /></div>' },
  CardHeader: { template: '<div><slot /></div>' },
  CardTitle: { template: '<div><slot /></div>' },
  CardDescription: { template: '<div><slot /></div>' },
  CardContent: { template: '<div><slot /></div>' },
}))
vi.mock('@/components/ui/label', () => ({
  Label: { template: '<label><slot /></label>' },
}))
vi.mock('@/components/ui/input', () => ({
  Input: { template: '<input v-bind="$attrs" />', props: ['modelValue'], emits: ['update:modelValue'] },
}))
vi.mock('@/components/ui/badge', () => ({
  Badge: { template: '<span><slot /></span>' },
}))
vi.mock('@/components/ui/switch', () => ({
  Switch: { template: '<input type="checkbox" v-bind="$attrs" />', props: ['checked'], emits: ['update:checked'] },
}))
vi.mock('@/components/ui/checkbox', () => ({
  Checkbox: { template: '<input type="checkbox" v-bind="$attrs" />', props: ['checked'], emits: ['update:checked'] },
}))
vi.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: { template: '<div><slot /></div>' },
}))
vi.mock('@/components/ui/tabs', () => ({
  Tabs: { template: '<div><slot /></div>', props: ['modelValue'], emits: ['update:modelValue'] },
  TabsContent: { template: '<div><slot /></div>' },
  TabsList: { template: '<div><slot /></div>' },
  TabsTrigger: { template: '<button v-bind="$attrs"><slot /></button>' },
}))
vi.mock('@/components/ui/dialog', () => ({
  Dialog: { template: '<div><slot /></div>', props: ['open'], emits: ['update:open'] },
  DialogContent: { template: '<div><slot /></div>' },
  DialogDescription: { template: '<div><slot /></div>' },
  DialogFooter: { template: '<div><slot /></div>' },
  DialogHeader: { template: '<div><slot /></div>' },
  DialogTitle: { template: '<div><slot /></div>' },
}))
vi.mock('@/components/ui/alert', () => ({
  Alert: { template: '<div><slot /></div>' },
  AlertTitle: { template: '<div><slot /></div>' },
  AlertDescription: { template: '<div><slot /></div>' },
}))
vi.mock('@/components/ui/accordion', () => ({
  Accordion: { template: '<div><slot /></div>' },
  AccordionItem: { template: '<div><slot /></div>' },
  AccordionTrigger: { template: '<button v-bind="$attrs"><slot /></button>' },
  AccordionContent: { template: '<div><slot /></div>' },
}))

vi.mock('@/components/ui/select', () => {
  const Select = defineComponent({
    name: 'Select',
    props: {
      modelValue: { type: String, default: '' },
    },
    emits: ['update:modelValue'],
    template: '<div><slot /></div>',
  })
  return {
    Select,
    SelectTrigger: { template: '<div><slot /></div>' },
    SelectValue: { template: '<div><slot /></div>' },
    SelectContent: { template: '<div><slot /></div>' },
    SelectGroup: { template: '<div><slot /></div>' },
    SelectLabel: { template: '<div><slot /></div>' },
    SelectItem: { template: '<div><slot /></div>' },
  }
})

describe('PermissionConfig.vue', () => {
  it('shows locked state for system role by default', () => {
    const wrapper = mount(PermissionConfig)
    expect(wrapper.text()).toContain('系统内置角色')

    const bulkBtn = wrapper.findAll('button').find((b) => b.text().includes('勾选筛选'))
    expect(bulkBtn?.attributes('disabled')).toBeDefined()
  })

  it('bulk select increases granted count for normal role', async () => {
    const wrapper = mount(PermissionConfig)

    const selects = wrapper.findAllComponents({ name: 'Select' })
    selects[0].vm.$emit('update:modelValue', '2')
    await wrapper.vm.$nextTick()

    const extract = () => {
      const m = wrapper.text().match(/(\d+)\s*\/\s*(\d+)/)
      if (!m) throw new Error('count not found')
      return { granted: Number(m[1]), total: Number(m[2]) }
    }

    const before = extract()
    const bulkBtn = wrapper.findAll('button').find((b) => b.text().includes('勾选筛选'))
    await bulkBtn?.trigger('click')
    await wrapper.vm.$nextTick()

    const after = extract()
    expect(after.total).toBe(before.total)
    expect(after.granted).toBeGreaterThan(before.granted)
  })
})

