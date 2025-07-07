



<script setup>
import { RouterLink } from 'vue-router'
import { ref } from "vue";

// 부모로부터 onItemClick 이라는 이름의 함수를 prop으로 받습니다.
const props = defineProps({
  onItemClick: {
    type: Function,
    default: () => {} // 기본값 설정으로 에러 방지
  }
});

// 버튼을 클릭했을 때 실행될 함수
const handleLinkClick = () => {
  // 부모로부터 받은 함수를 실행합니다.
  props.onItemClick(); 
};

const itemsCompany = ref([
    { route: '0', label: 'YieldMax'},
    { route: '1', label: 'Roundhill'},
    { route: '2', label: 'ETC' }
]);

const YieldMaxCoveredCall = ref([
    { route: '/stock/tsly', label: 'TSLY' },
    { route: '/stock/oark', label: 'OARK' },
    { route: '/stock/aply', label: 'APLY' },
    { route: '/stock/nvdy', label: 'NVDY' },
    { route: '/stock/amzy', label: 'AMZY' },
    { route: '/stock/fby', label: 'FBY' },
    { route: '/stock/gooy', label: 'GOOY' },
    { route: '/stock/cony', label: 'CONY' },
    { route: '/stock/nfly', label: 'NFLY' },
    { route: '/stock/diso', label: 'DISO' },
    { route: '/stock/msfo', label: 'MSFO' },
    { route: '/stock/xomo', label: 'XOMO' },
    { route: '/stock/jpmo', label: 'JPMO' },
    { route: '/stock/amdy', label: 'AMDY' },
    { route: '/stock/pypy', label: 'PYPY' },
    { route: '/stock/sqy', label: 'XYZY' },
    { route: '/stock/mrny', label: 'MRNY' },
    { route: '/stock/aiyy', label: 'AIYY' },
    { route: '/stock/msty', label: 'MSTY' },
    { route: '/stock/ybit', label: 'YBIT' },
    { route: '/stock/gdxy', label: 'GDXY' },
    { route: '/stock/snoy', label: 'SNOY' },
    { route: '/stock/abny', label: 'ABNY' },
    { route: '/stock/babo', label: 'BABO' },
    { route: '/stock/tsmy', label: 'TSMY' },
    { route: '/stock/smcy', label: 'SMCY' },
    { route: '/stock/plty', label: 'PLTY' },
    { route: '/stock/maro', label: 'MARO' },
    { route: '/stock/cvny', label: 'CVNY' },
    { route: '/stock/hooy', label: 'HOOY' },
    { route: '/stock/brkc', label: 'BRKC' }
]);

const YieldMaxFundofFunds = ref([
    { route: '/stock/ymax', label: 'YMAX' },
    { route: '/stock/ymag', label: 'YMAG' },
    { route: '/stock/fivy', label: 'FIVY' },
    { route: '/stock/feat', label: 'FEAT' }
]);

const YieldMaxUltra = ref([
    { route: '/stock/ulty', label: 'ULTY' }
]);

const YieldMaxShortOptionIncome = ref([
    { route: '/stock/crsh', label: 'CRSH' },
    { route: '/stock/fiat', label: 'FIAT' },
    { route: '/stock/dips', label: 'DIPS' },
    { route: '/stock/yqqq', label: 'YQQQ' },
    { route: '/stock/wntr', label: 'WNTR' }
]);

const YieldMaxTarget12 = ref([
    { route: '/stock/bigy', label: 'BIGY' },
    { route: '/stock/soxy', label: 'SOXY' },
    { route: '/stock/rnty', label: 'RNTY' }
]);

const YieldMaxDorseyWright = ref([
    { route: '/stock/feat', label: 'FEAT' },
    { route: '/stock/fivy', label: 'FIVY' }
]);

const YieldMaxPortfolio = ref([
    { route: '/stock/lfgy', label: 'LFGY' },
    { route: '/stock/gpty', label: 'GPTY' },
    { route: '/stock/chpy', label: 'CHPY' }
]);

const YieldMax0DTE = ref([
    { route: '/stock/sdty', label: 'SDTY' },
    { route: '/stock/qdty', label: 'QDTY' },
    { route: '/stock/rdty', label: 'RDTY' }
]);

const RoundhillIncome = ref([
    { route: '/stock/xdte', label: 'XDTE' },
    { route: '/stock/qdte', label: 'QDTE' },
    { route: '/stock/rdte', label: 'RDTE' },
    { route: '/stock/xpay', label: 'XPAY' },
    { route: '/stock/ybtc', label: 'YBTC' },
    { route: '/stock/yeth', label: 'YETH' },
    { route: '/stock/week', label: 'WEEK' },
    { route: '/stock/magy', label: 'MAGY' }
]);

const RoundhillWeeklyPay = ref([
    { route: '/stock/aapw', label: 'AAPW' },
    { route: '/stock/amzw', label: 'AMZW' },
    { route: '/stock/brkw', label: 'BRKW' },
    { route: '/stock/coiw', label: 'COIW' },
    { route: '/stock/hoow', label: 'HOOW' },
    { route: '/stock/metw', label: 'METW' },
    { route: '/stock/nflw', label: 'NFLW' },
    { route: '/stock/nvdw', label: 'NVDW' },
    { route: '/stock/pltw', label: 'PLTW' },
    { route: '/stock/tslw', label: 'TSLW' }
]);

const DefianceIncome = ref([
    { route: '/stock/qqqy', label: 'QQQY' },
    { route: '/stock/wdte', label: 'WDTE' },
    { route: '/stock/iwmy', label: 'IWMY' },
    { route: '/stock/spyt', label: 'SPYT' },
    { route: '/stock/qqqt', label: 'QQQT' },
    { route: '/stock/usoy', label: 'USOY' },
    { route: '/stock/gldy', label: 'GLDY' },
    { route: '/stock/mst', label: 'MST' },
]);

const RexIncome = ref([
    { route: '/stock/coii', label: 'COII' },
    { route: '/stock/msii', label: 'MSII' },
    { route: '/stock/nvii', label: 'NVII' },
    { route: '/stock/tsii', label: 'TSII' },
]);
const JPMorganIncome = ref([
    { route: '/stock/jepi', label: 'JEPI' },
    { route: '/stock/jepq', label: 'JEPQ' },
    { route: '/stock/jfli', label: 'JFLI' },
]);

const GranitesharesYieldBOOST = ref([
    { route: '/stock/xbty', label: 'XBTY' },
    { route: '/stock/nvyy', label: 'NVYY' },
    { route: '/stock/tqqy', label: 'TQQY' },
    { route: '/stock/yspy', label: 'YSPY' },
    { route: '/stock/tsyy', label: 'TSYY' },
]);

const SchwabDividend = ref([
    { route: '/stock/schd', label: 'SCHD' },
]);
</script>



<template>
        <Tabs value="1">
            <TabList class="flex-wrap">
                <Tab v-for="tab in itemsCompany" :key="tab.label" :value="tab.route"  class="flex items-center gap-2 text-lg col-4 md:col-4 justify-content-center">
                    <span class="whitespace-nowrap">{{ tab.label }}</span>
                </Tab>
            </TabList>
            <TabPanels>
                <TabPanel value="0">
                    <Fieldset legend="YieldMax™ Covered Call ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxCoveredCall" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Fund of Funds ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxFundofFunds" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Ultra ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxUltra" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Short Option Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxShortOptionIncome" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Target 12™ ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxTarget12" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Dorsey Wright ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxDorseyWright" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ Portfolio ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMaxPortfolio" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="YieldMax™ 0DTE ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in YieldMax0DTE" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                </TabPanel>
                <TabPanel value="1">
                    <Fieldset legend="Roundhill Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in RoundhillIncome" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="Roundhill 0DTE ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in RoundhillWeeklyPay" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                </TabPanel>
                <TabPanel value="2">

                    <Fieldset legend="Schwab Dividend ETF">
                        <Button asChild v-slot="slotProps" v-for="tab in SchwabDividend" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="JP Morgan Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in JPMorganIncome" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="Defiance Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in DefianceIncome" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="Graniteshares YieldBOOST ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in GranitesharesYieldBOOST" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    <Fieldset legend="REX Weekly Paying Growth + Income ETFs">
                        <Button asChild v-slot="slotProps" v-for="tab in RexIncome" variant="text">
                            <RouterLink @click="handleLinkClick"  :to="tab.route" :class="slotProps.class">{{ tab.label }}</RouterLink>
                        </Button>
                    </Fieldset>
                    
                </TabPanel>
            </TabPanels>
        </Tabs>

</template>
