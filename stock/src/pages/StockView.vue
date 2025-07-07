<script setup>
import { ref, watch, onMounted, computed } from 'vue'; // computed 임포트
import { useRoute } from 'vue-router';
import { joinURL } from 'ufo'; 

// PrimeVue 컴포넌트
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner';
import Breadcrumb from 'primevue/breadcrumb';

const route = useRoute();
const stockData = ref([]);
const isLoading = ref(true);
const error = ref(null);
const ticker = ref(route.params.ticker);

// --- 1. 동적 컬럼 생성을 위한 로직 ---
const columns = computed(() => {
  if (stockData.value.length === 0) {
    return []; // 데이터가 없으면 빈 배열 반환
  }
  // 첫 번째 데이터 아이템의 모든 키(key)를 가져와서 헤더로 사용
  return Object.keys(stockData.value[0]).map(key => ({
    field: key,
    header: key
  }));
});

const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  stockData.value = [];
  
  const url = joinURL(import.meta.env.BASE_URL, `data/${tickerName.toLowerCase()}.json`);
  console.log('Fetching data from URL:', url);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`파일을 찾을 수 없습니다: ${url} (${response.status})`);
    }
    stockData.value = await response.json();
  } catch (err) {
    console.error(`Error fetching data for ${tickerName}:`, err);
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

// --- 2. Breadcrumb 반응성 문제 해결 ---
const home = ref({
    icon: 'pi pi-home',
    route: '/' // 홈페이지 경로는 '/'가 더 일반적입니다.
});

// Breadcrumb 아이템을 computed 속성으로 만듭니다.
const items = computed(() => [
    { label: 'ETF 목록', route: '/' }, // 예시 경로
    { label: ticker.value.toUpperCase() } // 이제 ticker의 변경에 따라 자동으로 업데이트됩니다.
]);

// URL의 :ticker 파라미터가 변경될 때마다 데이터를 다시 불러옴
watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    ticker.value = newTicker; // ticker ref 업데이트
    fetchData(newTicker);
  }
}, { immediate: true }); // immediate: true 옵션으로 컴포넌트 로드 시 즉시 실행

</script>

<template>
  <div class="card">
    <!-- 이제 items는 computed 속성이므로 항상 최신 상태를 반영합니다. -->
    <Breadcrumb :home="home" :model="items">
      <template #item="{ item, props }">
        <router-link v-if="item.route" v-slot="{ href, navigate }" :to="item.route" custom>
          <a :href="href" v-bind="props.action" @click="navigate">
            <span :class="[item.icon, 'text-color']" />
            <span class="text-primary font-semibold">{{ item.label }}</span>
          </a>
        </router-link>
        <a v-else :href="item.url" :target="item.target" v-bind="props.action">
          <span class="text-surface-700 dark:text-surface-0">{{ item.label }}</span>
        </a>
      </template>
    </Breadcrumb>

    <h2 class="mt-4">{{ ticker.toUpperCase() }} 분배금 정보</h2>
    
    <div v-if="isLoading" class="flex justify-center items-center h-48">
      <ProgressSpinner />
    </div>
    
    <div v-else-if="error">
      <p class="text-red-500">{{ error }}</p>
    </div>
    
    <!-- v-else와 v-if를 함께 사용할 수 없으므로, template으로 감싸줍니다. -->
    <template v-else-if="stockData.length > 0">
      <DataTable :value="stockData" responsiveLayout="scroll">
        <!-- v-for를 사용해 동적으로 컬럼을 렌더링합니다. -->
        <Column v-for="col in columns" :key="col.field" :field="col.field" :header="col.header"></Column>
      </DataTable>
    </template>
    
    <div v-else>
      <p>표시할 데이터가 없습니다.</p>
    </div>
  </div>
</template>