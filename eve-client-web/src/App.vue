<script setup lang="ts">
import {
  NConfigProvider,
  NDialogProvider,
  NGlobalStyle,
  NLoadingBarProvider,
  NMessageProvider,
  darkTheme,
  type GlobalThemeOverrides,
} from 'naive-ui'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#00fefe',
    primaryColorHover: '#33ffff',
    primaryColorPressed: '#00c7c7',
    primaryColorSuppl: '#00fefe',
    infoColor: '#00fefe',
    successColor: '#00d68f',
    warningColor: '#f5c542',
    errorColor: '#ff4d4d',
    bodyColor: '#0a0c10',
    cardColor: '#14181f',
    modalColor: '#14181f',
    popoverColor: '#14181f',
    borderColor: '#2a2f3a',
    textColorBase: '#e0e0e0',
    textColor1: '#e0e0e0',
    textColor2: '#96a2b8',
    textColor3: '#6d7788',
    placeholderColor: '#5a6578',
  },
  Layout: {
    color: '#0a0c10',
    siderColor: '#10141b',
    headerColor: '#14181f',
  },
  Menu: {
    itemColorActive: 'rgba(0, 254, 254, 0.12)',
    itemTextColorActive: '#00fefe',
    itemIconColorActive: '#00fefe',
    itemTextColorHover: '#00fefe',
    itemIconColorHover: '#00fefe',
  },
  Card: {
    color: '#14181f',
    borderColor: '#2a2f3a',
  },
}
</script>

<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-loading-bar-provider>
      <n-message-provider>
        <n-dialog-provider>
          <router-view />
        </n-dialog-provider>
      </n-message-provider>
    </n-loading-bar-provider>
    <n-global-style />
  </n-config-provider>
</template>
