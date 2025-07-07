



<script setup>
import { ref } from "vue";

import SidebarCompany from "./SidebarCompany.vue";
import SidebarPeriod from "./SidebarPeriod.vue";

// AppTopbar로부터 close-sidebar 라는 이름의 함수를 prop으로 받습니다.
const props = defineProps({
  closeSidebar: {
    type: Function,
    required: true
  }
});

</script>


<template>
    <div class="card">
        <Tabs value="0">
            <TabList>
                <Tab value="0" class="flex items-center gap-2 text-lg col-6 justify-content-center">
                    <i class="pi pi-building text-3xl" />
                    <span class="font-bold whitespace-nowrap">회사별</span>
                </Tab>
                <Tab value="1" class="flex items-center gap-2 text-lg col-6 justify-content-center">
                    <i class="pi pi-calendar text-3xl" />
                    <span class="font-bold whitespace-nowrap">일정별</span>
                </Tab>
            </TabList>
            <TabPanels>
                <TabPanel value="0">
                    <SidebarCompany :on-item-click="closeSidebar" />
                </TabPanel>
                <TabPanel value="1">
                    <SidebarPeriod :on-item-click="closeSidebar" />
                </TabPanel>
            </TabPanels>
        </Tabs>
    </div>

</template>