



<script setup>
import { RouterLink } from 'vue-router'
import { ref } from "vue";

const itemsCompany = ref([
    { route: '0', label: 'YieldMax'},
    { route: '1', label: 'Roundhill'},
    { route: '2', label: 'Defiance'},
    { route: '3', label: 'JP Morgan' }
]);

const LinkYieldMax = ref([
    { route: '/', label: 'YieldMax'},
    { route: '/', label: 'Roundhill'},
    { route: '/', label: 'Defiance'},
    { route: '/', label: 'JP Morgan' }
]);

</script>



<template>
        <Tabs value="0">
            <TabList class="flex-wrap">
                <Tab v-for="tab in itemsCompany" :key="tab.label" :value="tab.route"  class="flex items-center gap-2 text-lg col-6 md:col-3 justify-content-center">
                    <span class="whitespace-nowrap">{{ tab.label }}</span>
                </Tab>
            </TabList>
            <TabPanels>
                <TabPanel value="0">
                    <ul>
                        <li><RouterLink to="/">Home</RouterLink></li>
                        <li><RouterLink to="/about">About</RouterLink></li>
                        <li><RouterLink to="/dashboard">Dashboard</RouterLink></li>
                    </ul>
                </TabPanel>
                <TabPanel value="1">
                    <Fieldset legend="YieldMax™ Covered Call ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ Fund of Funds ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ Ultra ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ Short Option Income ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ Target 12™ ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ Dorsey Wright ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ Portfolio ETFs"></Fieldset>
                    <Fieldset legend="YieldMax™ 0DTE ETFs"></Fieldset>
                    <Fieldset legend="YieldMax UCITS Funds"></Fieldset>
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
