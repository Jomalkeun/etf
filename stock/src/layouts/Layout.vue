<script setup>
import { RouterView } from 'vue-router'
import AppTopbar from "./AppTopbar.vue";
import Breadcrumb from '../utils/Breadcrumb.vue'
</script>

<template>
    <div class="layout-container">
        <div class="topbar">
            <div class="topbar-container">
                <Breadcrumb icon='pi-money-bill' brand="YieldMax" title="YMAX" msg="상세 메세지" />
                <AppTopbar />
            </div>
        </div>
        
        <div class="layout-grid">
            <RouterView />
        </div>
    </div>
</template>
