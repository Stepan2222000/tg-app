import type { Config, TaskAssignment } from '../types';

export const mockConfig: Config = {
  simple_task_price: 50,
  phone_task_price: 150,
  min_withdrawal: 500,
  max_active_tasks: 10,
  referral_commission: 0.5,
  task_lock_hours: 24,
  instructions:
    'Найдите объявление на Avito, скопируйте текст сообщения и отправьте продавцу. Сделайте скриншоты переписки.',
};

export const createMockActiveTasks = (): TaskAssignment[] => {
  const now = new Date();
  const deadline1 = new Date(now.getTime() + 18 * 60 * 60 * 1000); // +18 hours
  const deadline2 = new Date(now.getTime() + 6 * 60 * 60 * 1000); // +6 hours
  const deadline3 = new Date(now.getTime() + 22 * 60 * 60 * 1000); // +22 hours

  return [
    {
      id: 1,
      task_id: 101,
      user_id: 123456789,
      status: 'assigned',
      deadline: deadline1.toISOString(),
      phone_number: null,
      screenshots: [],
      assigned_at: now.toISOString(),
      submitted_at: null,
      created_at: now.toISOString(),
      task: {
        id: 101,
        type: 'simple',
        avito_url:
          'https://www.avito.ru/moskva/telefony/iphone_13_128gb_3041234567',
        message_text:
          'Здравствуйте! Интересует ваш iPhone. Актуально? Можно посмотреть сегодня?',
        price: 50,
        is_available: false,
        created_at: now.toISOString(),
        updated_at: now.toISOString(),
      },
    },
    {
      id: 2,
      task_id: 102,
      user_id: 123456789,
      status: 'assigned',
      deadline: deadline2.toISOString(),
      phone_number: null,
      screenshots: [],
      assigned_at: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
      submitted_at: null,
      created_at: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
      task: {
        id: 102,
        type: 'phone',
        avito_url:
          'https://www.avito.ru/spb/kvartiry/2-k_kvartira_58_m_3545678901',
        message_text:
          'Добрый день! Квартира свободна? Можно уточнить детали по телефону?',
        price: 150,
        is_available: false,
        created_at: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString(),
      },
    },
    {
      id: 3,
      task_id: 103,
      user_id: 123456789,
      status: 'assigned',
      deadline: deadline3.toISOString(),
      phone_number: null,
      screenshots: [],
      assigned_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      submitted_at: null,
      created_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      task: {
        id: 103,
        type: 'simple',
        avito_url:
          'https://www.avito.ru/novosibirsk/noutbuki/macbook_pro_16_2023_4556789012',
        message_text: 'Привет! MacBook в отличном состоянии? Торг возможен?',
        price: 50,
        is_available: false,
        created_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      },
    },
  ];
};
