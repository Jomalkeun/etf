<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

// PrimeVue 컴포넌트 임포트
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import Tag from 'primevue/tag';
import ProgressSpinner from 'primevue/progressspinner';
import { FilterMatchMode } from '@primevue/core/api';

const router = useRouter();
const etfList = ref([]);
const isLoading = ref(true);
const error = ref(null);

// --- 필터링을 위한 상태 ---
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
    company: { value: null, matchMode: FilterMatchMode.IN },
    frequency: { value: null, matchMode: FilterMatchMode.EQUALS },
});

// 드롭다운 필터를 위한 고유값 목록 (동적으로 생성)
const companies = ref([]);
const frequencies = ref([]);

// --- 데이터 로딩 ---
onMounted(async () => {
    try {
        const response = await fetch('/nav.json'); // public 폴더의 nav.json 로드
        if (!response.ok) throw new Error('Navigation data not found');
        const data = await response.json();
        
        etfList.value = data.nav;

        // 필터용 고유값 목록 생성
        companies.value = [...new Set(data.nav.map(item => item.company))];
        frequencies.value = [...new Set(data.nav.map(item => item.frequency))];

    } catch (err) {
        console.error("Error fetching nav.json:", err);
        error.value = "ETF 목록을 불러오는 데 실패했습니다.";
    } finally {
        isLoading.value = false;
    }
});

// 행(Row) 클릭 시 해당 ETF 상세 페이지로 이동하는 함수
const onRowSelect = (event) => {
    const ticker = event.data.name;
    router.push(`/stock/${ticker.toLowerCase()}`);
};

// 지급주기에 따라 다른 색상의 태그를 보여주는 함수
const getFrequencySeverity = (frequency) => {
    switch (frequency) {
        case 'Weekly':
            return 'success';
        case 'Monthly':
            return 'info';
        case 'Quarterly':
            return 'warning';
        default:
            return 'contrast';
    }
};
</script>

<template>
    <div class="card">
        <h2>전체 ETF 목록</h2>
        <p>원하는 ETF를 검색하거나 필터링하여 찾아보세요. 행을 클릭하면 상세 정보 페이지로 이동합니다.</p>

        <div v-if="isLoading" class="flex justify-center items-center h-48">
            <ProgressSpinner />
        </div>
        <div v-else-if="error" class="text-red-500">{{ error }}</div>
        
        <DataTable v-else :value="etfList" v-model:filters="filters" filterDisplay="row"
                   dataKey="name" paginator :rows="20" :rowsPerPageOptions="[10, 20, 50, 100]"
                   selectionMode="single" @rowSelect="onRowSelect"
                   :globalFilterFields="['name', 'company', 'frequency']"
                   class="p-datatable-sm" stripedRows>
            
            <template #header>
                <div class="flex justify-end">
                    <span class="p-input-icon-left">
                        <i class="pi pi-search" />
                        <InputText v-model="filters['global'].value" placeholder="전체 검색" />
                    </span>
                </div>
            </template>
            
            <template #empty>
                <div class="text-center p-4">검색 결과가 없습니다.</div>
            </template>

            <Column field="name" header="티커" :showFilterMenu="false" sortable>
                <template #body="{ data }">
                    <span class="font-bold">{{ data.name }}</span>
                </template>
                <template #filter="{ filterModel, filterCallback }">
                    <InputText v-model="filterModel.value" @input="filterCallback()" placeholder="티커 검색" class="p-column-filter" />
                </template>
            </Column>

            <Column field="company" header="운용사" :showFilterMenu="false" sortable>
                <template #filter="{ filterModel, filterCallback }">
                    <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="companies" placeholder="운용사 선택" showClear class="p-column-filter">
                        <template #option="slotProps">
                            <span>{{ slotProps.option }}</span>
                        </template>
                    </Dropdown>
                </template>
            </Column>

            <Column field="frequency" header="지급주기" :showFilterMenu="false" sortable>
                <template #body="{ data }">
                    <Tag :value="data.frequency" :severity="getFrequencySeverity(data.frequency)" />
                </template>
                <template #filter="{ filterModel, filterCallback }">
                     <Dropdown v-model="filterModel.value" @change="filterCallback()" :options="frequencies" placeholder="주기 선택" showClear class="p-column-filter">
                        <template #option="slotProps">
                            <Tag :value="slotProps.option" :severity="getFrequencySeverity(slotProps.option)" />
                        </template>
                    </Dropdown>
                </template>
            </Column>
        </DataTable>
    </div>
</template>