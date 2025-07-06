<script setup>
import { RouterLink } from 'vue-router'
import { ref } from "vue";

const itemsCompany = ref([
    { route: '0', label: 'Quarterly' },
    { route: '1', label: 'Monthly' },
    { route: '2', label: '4 Week' },
    { route: '3', label: 'Weekly' }
]);
</script>

<template>
        <Tabs value="0">
            <TabList class="flex-wrap">
            <Tab v-for="tab in itemsCompany" :key="tab.label" :value="tab.route"
                class="flex items-center gap-2 text-lg col-6 md:col-3 justify-content-center">
                    <span class="whitespace-nowrap">{{ tab.label }}</span>
                </Tab>
            </TabList>
            <TabPanels>
                <TabPanel value="0">
                    <ul>
                    <li>
                        <RouterLink to="/">Home</RouterLink>
                    </li>
                    <li>
                        <RouterLink to="/about">About</RouterLink>
                    </li>
                    <li>
                        <RouterLink to="/dashboard">Dashboard</RouterLink>
                    </li>
                    </ul>
                </TabPanel>
                <TabPanel value="1">
                    11111111
                </TabPanel>
                <TabPanel value="2">
                    2222222222
                </TabPanel>
                <TabPanel value="3">
                    3333333
                </TabPanel>
            </TabPanels>
        </Tabs>

</template>
