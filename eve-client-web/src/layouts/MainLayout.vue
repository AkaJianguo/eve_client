<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NIcon,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
  NMenu,
  NTag,
  type MenuOption,
} from 'naive-ui'
import { Boxes, Factory, LayoutDashboard, LineChart, LogOut, Orbit, Search, User, Wallet } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const renderIcon = (icon: typeof LayoutDashboard) => () => h(NIcon, null, { default: () => h(icon) })

const menuOptions: MenuOption[] = [
  {
    label: () => h(RouterLink, { to: '/profile' }, { default: () => '飞行员档案' }),
    key: '/profile',
    icon: renderIcon(User),
  },
  {
    label: () => h(RouterLink, { to: '/wallet' }, { default: () => '财务中心' }),
    key: '/wallet',
    icon: renderIcon(Wallet),
  },
  {
    label: () => h(RouterLink, { to: '/assets' }, { default: () => '资产清单' }),
    key: '/assets',
    icon: renderIcon(Boxes),
  },
  {
    label: '市场中心',
    key: 'market-center',
    icon: renderIcon(LineChart),
    children: [
      {
        label: () => h(RouterLink, { to: '/market' }, { default: () => '市场情报' }),
        key: '/market',
        icon: renderIcon(LineChart),
      },
      {
        label: () => h(RouterLink, { to: '/market-browser' }, { default: () => '市场浏览器' }),
        key: '/market-browser',
        icon: renderIcon(Search),
      },
    ],
  },
  {
    label: () => h(RouterLink, { to: '/dashboard' }, { default: () => '控制台' }),
    key: '/dashboard',
    icon: renderIcon(LayoutDashboard),
  },
  {
    label: () => h(RouterLink, { to: '/industry' }, { default: () => '工业监控' }),
    key: '/industry',
    icon: renderIcon(Factory),
  },
]

const activeKey = computed(() => route.path)
const expandedKeys = ref<string[]>(route.path.startsWith('/market') ? ['market-center'] : [])
const pilotName = computed(() => authStore.character?.name || '未识别飞行员')

watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/market') && !expandedKeys.value.includes('market-center')) {
      expandedKeys.value = [...expandedKeys.value, 'market-center']
    }
  },
  { immediate: true },
)

function handleUpdateExpandedKeys(keys: string[]) {
  expandedKeys.value = keys
}

async function handleLogout() {
  authStore.logout()
  await router.push('/login')
}
</script>

<template>
  <n-layout has-sider position="absolute" :class="$style.shell">
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="72"
      :width="240"
      show-trigger
      :class="$style.sider"
    >
      <div :class="$style.brand">
        <div :class="$style.brandIcon">
          <Orbit :size="18" />
        </div>
        <div :class="$style.brandText">
          <strong>EVE OPS</strong>
          <span>Industrial Control Grid</span>
        </div>
      </div>
      <n-menu
        :value="activeKey"
        :options="menuOptions"
        :expanded-keys="expandedKeys"
        @update:expanded-keys="handleUpdateExpandedKeys"
        :collapsed-width="72"
        :collapsed-icon-size="22"
        :class="$style.menu"
      />
      <div :class="$style.siderFooter">
        <n-tag size="small" type="info" :bordered="false">Tranquility</n-tag>
      </div>
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered :class="$style.header">
        <div>
          <div :class="$style.title">EVE 工业监控指挥系统</div>
          <div :class="$style.subtitle">高密度工单、资产与产业链路观察台</div>
        </div>
        <div :class="$style.headerActions">
          <n-tag type="info" :bordered="false">{{ pilotName }}</n-tag>
          <n-tag type="warning" :bordered="false">Omega Required</n-tag>
          <n-button tertiary type="primary" @click="handleLogout">
            <template #icon>
              <n-icon><LogOut :size="16" /></n-icon>
            </template>
            退出
          </n-button>
        </div>
      </n-layout-header>

      <n-layout-content :class="$style.content" content-style="padding: 24px;" :native-scrollbar="false">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<style module lang="scss">
.shell {
  height: 100vh;
  background: transparent;
}

.sider {
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(20, 24, 31, 0.98) 0%, rgba(10, 12, 16, 0.98) 100%);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.03);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 18px 18px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.brandIcon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(0, 254, 254, 0.25);
  border-radius: 8px;
  color: var(--eve-cyan);
  background: rgba(0, 254, 254, 0.08);
}

.brandText {
  display: flex;
  flex-direction: column;
  gap: 2px;

  strong {
    font-size: 14px;
    color: var(--eve-text-main);
    letter-spacing: 0.12em;
  }

  span {
    font-size: 11px;
    color: rgba(224, 224, 224, 0.52);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
}

.menu {
  padding: 14px 10px;
}

.siderFooter {
  margin-top: auto;
  padding: 16px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  height: 72px;
  padding: 0 24px;
  background: rgba(20, 24, 31, 0.9);
  backdrop-filter: blur(12px);
}

.title {
  color: var(--eve-cyan);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.subtitle {
  margin-top: 4px;
  color: rgba(224, 224, 224, 0.56);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.headerActions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.content {
  background: transparent;
}
</style>