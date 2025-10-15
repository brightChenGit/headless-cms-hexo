
export interface DeployStep {
    name: string;
    status: 'pending' | 'running' | 'success' | 'failure';
    message: string;
}

export interface DeployStatusResponse {
    task_id: string | null;
    status: '' | 'queued' | 'running' | 'success' | 'failure';
    message: string;
    triggered_by: string;
    steps: DeployStep[];
    created_at: number | null; // Unix timestamp
    can_deploy?: boolean; // 可选，后端返回或前端计算
}
export interface DeployStep {
    name: string;
    status: 'pending' | 'running' | 'success' | 'failure';
    message: string;
}

export interface DeployStatusResponse {
    task_id: string | null;
    status: '' | 'queued' | 'running' | 'success' | 'failure';
    message: string;
    triggered_by: string;
    steps: DeployStep[];
    created_at: number | null; // Unix timestamp
    can_deploy?: boolean; // 可选，后端返回或前端计算
}