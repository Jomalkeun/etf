



<script setup>
import { RouterLink } from 'vue-router'
import { ref } from "vue";

const itemsCompany = ref([
    { route: '0', label: 'YieldMax'},
    { route: '1', label: 'Roundhill'},
    { route: '2', label: 'Defiance'},
    { route: '3', label: 'JP Morgan' }
]);

const LinkYieldMaxCoveredCall = ref([
    { route: '/tsly', label: 'TSLY' },
    { route: '/oark', label: 'OARK' },
    { route: '/aply', label: 'APLY' },
    { route: '/nvdy', label: 'NVDY' },
    { route: '/amzy', label: 'AMZY' },
    { route: '/fby', label: 'FBY' },
    { route: '/gooy', label: 'GOOY' },
    { route: '/cony', label: 'CONY' },
    { route: '/nfly', label: 'NFLY' },
    { route: '/diso', label: 'DISO' },
    { route: '/msfo', label: 'MSFO' },
    { route: '/xomo', label: 'XOMO' },
    { route: '/jpmo', label: 'JPMO' },
    { route: '/amdy', label: 'AMDY' },
    { route: '/pypy', label: 'PYPY' },
    { route: '/sqy', label: 'XYZY' },
    { route: '/mrny', label: 'MRNY' },
    { route: '/aiyy', label: 'AIYY' },
    { route: '/msty', label: 'MSTY' },
    { route: '/ybit', label: 'YBIT' },
    { route: '/gdxy', label: 'GDXY' },
    { route: '/snoy', label: 'SNOY' },
    { route: '/abny', label: 'ABNY' },
    { route: '/babo', label: 'BABO' },
    { route: '/tsmy', label: 'TSMY' },
    { route: '/smcy', label: 'SMCY' },
    { route: '/plty', label: 'PLTY' },
    { route: '/maro', label: 'MARO' },
    { route: '/cvny', label: 'CVNY' },
    { route: '/hooy', label: 'HOOY' },
    { route: '/brkc', label: 'BRKC' }
]);

const LinkYieldMaxFundofFunds = ref([
    { route: '/ymax', label: 'YMAX' },
    { route: '/ymag', label: 'YMAG' },
    { route: '/fivy', label: 'FIVY' },
    { route: '/feat', label: 'FEAT' }
]);

const LinkYieldMaxUltra = ref([
    { route: '/ulty', label: 'ULTY' }
]);

const LinkYieldMaxShortOptionIncome = ref([
    { route: '/crsh', label: 'CRSH' },
    { route: '/fiat', label: 'FIAT' },
    { route: '/dips', label: 'DIPS' },
    { route: '/yqqq', label: 'YQQQ' },
    { route: '/wntr', label: 'WNTR' }
]);

const LinkYieldMaxTarget12 = ref([
    { route: '/bigy', label: 'BIGY' },
    { route: '/soxy', label: 'SOXY' },
    { route: '/rnty', label: 'SOXY' }
]);

const LinkYieldMaxDorseyWright = ref([
    { route: '/feat', label: 'FEAT' },
    { route: '/fivy', label: 'FIVY' }
]);

const LinkYieldMaxPortfolio = ref([
    { route: '/gpty', label: 'GPTY' },
    { route: '/chpy', label: 'CHPY' }
]);

const LinkYieldMax0DTE = ref([
    { route: '/sdty', label: 'SDTY' },
    { route: '/qdty', label: 'QDTY' },
    { route: '/rdty', label: 'RDTY' }
]);

const RoundhillIncome = ref([
    { route: '/xdte', label: 'XDTE' },
    { route: '/qdte', label: 'QDTE' },
    { route: '/rdte', label: 'RDTE' },
    { route: '/xpay', label: 'XPAY' },
    { route: '/ybtc', label: 'YBTC' },
    { route: '/yeth', label: 'YETH' },
    { route: '/week', label: 'WEEK' },
    { route: '/magy', label: 'MAGY' }
]);

const RoundhillWeeklyPay = ref([
    { route: '/aapw', label: 'AAPW' },
    { route: '/amzw', label: 'AMZW' },
    { route: '/brkw', label: 'BRKW' },
    { route: '/coiw', label: 'COIW' },
    { route: '/hoow', label: 'HOOW' },
    { route: '/metw', label: 'METW' },
    { route: '/nflw', label: 'NFLW' },
    { route: '/nvdw', label: 'NVDW' },
    { route: '/pltw', label: 'PLTW' },
    { route: '/tslw', label: 'TSLW' }
]);

const DefianceIncome = ref([
    { route: '/qqqy', label: 'QQQY' },
    { route: '/wdte', label: 'WDTE' },
    { route: '/iwmy', label: 'IWMY' },
    { route: '/spyt', label: 'SPYT' },
    { route: '/qqqt', label: 'QQQT' },
    { route: '/usoy', label: 'USOY' },
    { route: '/gldy', label: 'GLDY' },
]);

const JPMorganIncome = ref([
    { route: '/jepi', label: 'JEPI' },
    { route: '/jepq', label: 'JEPQ' },
    { route: '/jfli', label: 'JFLI' },
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
                    <Fieldset legend="YieldMax™ Covered Call ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxCoveredCall" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Fund of Funds ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxFundofFunds" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Ultra ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxUltra" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Short Option Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxShortOptionIncome" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Target 12™ ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxTarget12" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Dorsey Wright ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxDorseyWright" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Portfolio ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMaxPortfolio" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ 0DTE ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in LinkYieldMax0DTE" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                </TabPanel>
                <TabPanel value="1">
                    <Fieldset legend="Roundhill Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in RoundhillIncome" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="Roundhill 0DTE ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in RoundhillWeeklyPay" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                </TabPanel>
                <TabPanel value="2">
                    <Fieldset legend="Defiance Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in DefianceIncome" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                </TabPanel>
                <TabPanel value="3">
                    <Fieldset legend="JP Morgan Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in JPMorganIncome" variant="text">
                            <RouterLink :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                </TabPanel>
            </TabPanels>
        </Tabs>

</template>
