<script setup>
import { RouterView } from 'vue-router'
import AppTopbar from "./AppTopbar.vue";
import Breadcrumb from '../utils/Breadcrumb.vue'

import AppFooter from "../components/AppFooter.vue";
import StatsWidget from "../components/dashboard/StatsWidget.vue";
import SalesTrendWidget from "../components/dashboard/SalesTrendWidget.vue";
import RecentActivityWidget from "../components/dashboard/RecentActivityWidget.vue";
import ProductOverviewWidget from "../components/dashboard/ProductOverviewWidget.vue";
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
    <div class="layout-container">
        <AppTopbar />
        <div class="layout-grid">
            <StatsWidget />
            <div class="layout-grid-row">
                <SalesTrendWidget />
                <RecentActivityWidget />
            </div>
            <ProductOverviewWidget />
        </div>
        <AppFooter />
    </div>
</template>
