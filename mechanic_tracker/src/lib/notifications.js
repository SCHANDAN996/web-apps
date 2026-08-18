/**
 * Browser notification system for deadline alerts
 */

let notifInterval = null;

export function initNotifications(getPartsCallback) {
  if (!('Notification' in window)) return;

  // Request permission on first load
  if (Notification.permission === 'default') {
    Notification.requestPermission();
  }

  // Check every 30 minutes
  checkDeadlines(getPartsCallback);
  notifInterval = setInterval(() => checkDeadlines(getPartsCallback), 30 * 60 * 1000);
}

export function stopNotifications() {
  if (notifInterval) { clearInterval(notifInterval); notifInterval = null; }
}

async function checkDeadlines(getPartsCallback) {
  if (Notification.permission !== 'granted') return;

  const parts = await getPartsCallback();
  const now = new Date();

  for (const part of parts) {
    if (part.status === 'Refunded' || part.status === 'Returned') continue;
    if (!part.return_deadline) continue;

    const deadline = new Date(part.return_deadline);
    const hoursLeft = (deadline - now) / (1000 * 60 * 60);

    if (hoursLeft > 0 && hoursLeft <= 48) {
      const hrs = Math.floor(hoursLeft);
      new Notification('⚠️ Core Return Deadline!', {
        body: `${part.part_name} ($${part.core_fee}) expires in ${hrs}h. Return it now!`,
        icon: '/icons/icon-192.png',
        tag: `deadline-${part.id}`, // prevent duplicates
        requireInteraction: true
      });
    }
  }
}

export function getDeadlineInfo(deadlineStr) {
  if (!deadlineStr) return { text: 'No deadline', class: '', hoursLeft: Infinity };
  const deadline = new Date(deadlineStr);
  const now = new Date();
  const hoursLeft = (deadline - now) / (1000 * 60 * 60);
  const daysLeft = Math.ceil(hoursLeft / 24);

  if (hoursLeft < 0) return { text: 'EXPIRED', class: 'urgent-text', hoursLeft };
  if (hoursLeft <= 48) return { text: `${Math.floor(hoursLeft)}h left`, class: 'urgent-text', hoursLeft };
  if (daysLeft <= 7) return { text: `${daysLeft}d left`, class: 'warning-text', hoursLeft };
  return { text: `${daysLeft}d left`, class: '', hoursLeft };
}

export function getCardUrgencyClass(deadlineStr, status) {
  if (status === 'Refunded') return 'refunded';
  if (status === 'Returned') return 'safe';
  const { hoursLeft } = getDeadlineInfo(deadlineStr);
  if (hoursLeft < 0 || hoursLeft <= 48) return 'urgent';
  if (hoursLeft <= 168) return 'warning'; // 7 days
  return 'safe';
}
