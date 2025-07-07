



<script setup>
import { RouterLink } from 'vue-router'
import { ref } from "vue";

import SidebarCompany from "./SidebarCompany.vue";
import SidebarPeriod from "./SidebarPeriod.vue";
</script>


<template #container="{ closeCallback }">
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
                    <SidebarCompany />
                </TabPanel>
                <TabPanel value="1">
                    <SidebarPeriod />
                </TabPanel>
            </TabPanels>
        </Tabs>
    </div>

</template>