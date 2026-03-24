import type { MockUser } from '@/types/auth';

export const MOCK_USERS: MockUser[] = [
  {
    id: 'u-admin',
    username: 'admin',
    password: 'admin123',
    displayName: '系统管理员',
    role: 'admin',
  },
  {
    id: 'u-demo',
    username: 'demo',
    password: 'demo123456',
    displayName: '演示账号',
    role: 'demo',
  },
];
