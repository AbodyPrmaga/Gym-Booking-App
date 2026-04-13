const API_BASE = 'http://localhost:8000';
const state = {
    token: localStorage.getItem('gym_token') || null,
    tokenType: localStorage.getItem('gym_token_type') || 'bearer',
    profile: null,
    activeTab: 'dashboard',
    cached: {
        users: [],
        services: [],
        slots: [],
        bookings: []
    }
};

const app = document.getElementById('app');
const logoutButton = document.getElementById('logoutButton');
const messageBanner = document.getElementById('messageBanner');

logoutButton.addEventListener('click', handleLogout);

init();

function init() {
    if (state.token) {
        showDashboard();
        loadProfile();
    } else {
        renderAuthView();
    }
}

function setMessage(type, text) {
    const colors = {
        success: 'bg-emerald-50 border-emerald-200 text-emerald-700',
        error: 'bg-rose-50 border-rose-200 text-rose-700',
        info: 'bg-sky-50 border-sky-200 text-sky-700'
    };
    messageBanner.innerHTML = `<div class="rounded-2xl border px-4 py-3 ${colors[type] || colors.info}"><p class="text-sm">${text}</p></div>`;
    setTimeout(() => { messageBanner.innerHTML = ''; }, 6000);
}

function apiRequest(path, options = {}) {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const headers = options.headers || {};
    headers['Content-Type'] = 'application/json';
    if (state.token) {
        headers['Authorization'] = `${state.tokenType} ${state.token}`;
    }
    return fetch(url, { ...options, headers }).then(async (res) => {
        const contentType = res.headers.get('content-type') || '';
        const body = contentType.includes('application/json') ? await res.json() : null;
        if (!res.ok) {
            const message = body?.detail || body?.message || body || res.statusText;
            throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
        }
        return body;
    });
}

function queryString(params) {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            search.append(key, String(value));
        }
    });
    return search.toString() ? `?${search.toString()}` : '';
}

function renderAuthView() {
    logoutButton.classList.add('hidden');
    app.innerHTML = `
    <div class="grid gap-6 lg:grid-cols-2">
      <section class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/80">
        <h2 class="text-2xl font-semibold">Login</h2>
        <p class="mt-2 text-sm text-slate-500">Sign in to access the gym booking dashboard.</p>
        <form id="loginForm" class="mt-6 space-y-4">
          <label class="block text-sm font-medium text-slate-700">Email<input id="loginEmail" type="email" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
          <label class="block text-sm font-medium text-slate-700">Password<input id="loginPassword" type="password" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
          <button class="w-full rounded-2xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">Login</button>
        </form>
      </section>
      <section class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/80">
        <h2 class="text-2xl font-semibold">Register</h2>
        <p class="mt-2 text-sm text-slate-500">Create an account for the booking system.</p>
        <form id="registerForm" class="mt-6 space-y-4">
          <label class="block text-sm font-medium text-slate-700">Name<input id="registerName" type="text" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
          <label class="block text-sm font-medium text-slate-700">Email<input id="registerEmail" type="email" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
          <label class="block text-sm font-medium text-slate-700">Password<input id="registerPassword" type="password" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
          <button class="w-full rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">Register</button>
        </form>
      </section>
    </div>
  `;
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    try {
        const body = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        state.token = body.access_token;
        state.tokenType = body.token_type || 'bearer';
        localStorage.setItem('gym_token', state.token);
        localStorage.setItem('gym_token_type', state.tokenType);
        setMessage('success', 'Login successful. Loading dashboard...');
        showDashboard();
        await loadProfile();
    } catch (error) {
        setMessage('error', `Login failed: ${error.message}`);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    try {
        await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password })
        });
        setMessage('success', 'Registration successful. Please login with your new account.');
        document.getElementById('registerForm').reset();
    } catch (error) {
        setMessage('error', `Registration failed: ${error.message}`);
    }
}

function showDashboard() {
    logoutButton.classList.remove('hidden');
    renderDashboard();
    loadUsers();
    loadServices();
    loadSlots();
    loadBookings();
}

function renderDashboard() {
    app.innerHTML = `
    <div class="grid gap-6 xl:grid-cols-[280px_1fr]">
      <aside class="rounded-3xl bg-slate-950/95 p-6 text-white shadow-xl shadow-slate-200/5 xl:sticky xl:top-6">
        <div class="space-y-4">
          <div>
            <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Control Center</p>
            <h2 class="mt-3 text-2xl font-semibold">Navigation</h2>
          </div>
          <nav class="space-y-2" id="sidebarNav"></nav>
        </div>
      </aside>
      <main class="space-y-6">
        <section id="mainSection"></section>
      </main>
    </div>
  `;
    renderSidebar();
    renderMainSection();
}

function renderSidebar() {
    const tabs = [
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'about', label: 'Profile' },
        { id: 'users', label: 'Users' },
        { id: 'services', label: 'Services' },
        { id: 'slots', label: 'Slots' },
        { id: 'bookings', label: 'Bookings' },
        { id: 'create_service', label: 'New Service' },
        { id: 'create_slot', label: 'New Slot' },
        { id: 'create_booking', label: 'New Booking' }
    ];
    const nav = document.getElementById('sidebarNav');
    nav.innerHTML = tabs.map(tab => `
    <button data-tab="${tab.id}" class="w-full rounded-3xl px-4 py-3 text-left text-sm transition ${state.activeTab === tab.id ? 'bg-white text-slate-950 shadow-lg' : 'bg-slate-900/80 text-slate-300 hover:bg-slate-800/90 hover:text-white'}">
      ${tab.label}
    </button>
  `).join('');
    nav.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', () => {
            state.activeTab = button.dataset.tab;
            renderMainSection();
            renderSidebar();
        });
    });
}

function renderMainSection() {
    const section = document.getElementById('mainSection');
    section.innerHTML = '';
    if (state.activeTab === 'dashboard') {
        section.appendChild(renderDashboardSummary());
        section.appendChild(renderQuickActions());
    } else if (state.activeTab === 'about') {
        section.appendChild(renderProfileCard());
    } else if (state.activeTab === 'users') {
        section.appendChild(renderUsersView());
    } else if (state.activeTab === 'services') {
        section.appendChild(renderServicesView());
    } else if (state.activeTab === 'slots') {
        section.appendChild(renderSlotsView());
    } else if (state.activeTab === 'bookings') {
        section.appendChild(renderBookingsView());
    } else if (state.activeTab === 'create_service') {
        section.appendChild(renderServiceForm());
    } else if (state.activeTab === 'create_slot') {
        section.appendChild(renderSlotForm());
    } else if (state.activeTab === 'create_booking') {
        section.appendChild(renderBookingForm());
    }
}

function renderDashboardSummary() {
    const card = document.createElement('section');
    card.className = 'grid gap-6 sm:grid-cols-2';
    const profileStats = `
    <div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70">
      <h3 class="text-lg font-semibold">Logged in as</h3>
      <p class="mt-3 text-sm text-slate-600">${state.profile ? state.profile.name : 'Loading...'}</p>
      <p class="mt-1 text-sm text-slate-500">${state.profile ? state.profile.email : ''}</p>
    </div>
  `;
    const counts = `
    <div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70">
      <h3 class="text-lg font-semibold">Current counts</h3>
      <dl class="mt-4 grid gap-4 sm:grid-cols-3">
        <div class="rounded-2xl bg-slate-950/95 p-4 text-white">
          <dt class="text-xs uppercase tracking-[0.24em] text-slate-400">Users</dt>
          <dd class="mt-2 text-2xl font-semibold">${state.cached.users.length || '—'}</dd>
        </div>
        <div class="rounded-2xl bg-slate-950/95 p-4 text-white">
          <dt class="text-xs uppercase tracking-[0.24em] text-slate-400">Services</dt>
          <dd class="mt-2 text-2xl font-semibold">${state.cached.services.length || '—'}</dd>
        </div>
        <div class="rounded-2xl bg-slate-950/95 p-4 text-white">
          <dt class="text-xs uppercase tracking-[0.24em] text-slate-400">Bookings</dt>
          <dd class="mt-2 text-2xl font-semibold">${state.cached.bookings.length || '—'}</dd>
        </div>
      </dl>
    </div>
  `;
    card.innerHTML = profileStats + counts;
    return card;
}

function renderQuickActions() {
    const card = document.createElement('section');
    card.className = 'rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70';
    card.innerHTML = `
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 class="text-lg font-semibold">Quick actions</h3>
        <p class="mt-2 text-sm text-slate-500">Jump between important modules for service, slot, and booking management.</p>
      </div>
      <div class="grid gap-3 sm:grid-cols-3">
        <button data-tab="create_service" class="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">New service</button>
        <button data-tab="create_slot" class="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">New slot</button>
        <button data-tab="create_booking" class="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-200">New booking</button>
      </div>
    </div>
  `;
    card.querySelectorAll('button').forEach((button) => {
        button.addEventListener('click', () => {
            state.activeTab = button.dataset.tab;
            renderMainSection();
            renderSidebar();
        });
    });
    return card;
}

function renderProfileCard() {
    const card = document.createElement('section');
    card.className = 'rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70';
    const profileHtml = state.profile ? `
    <div class="grid gap-4 md:grid-cols-2">
      <div class="space-y-4">
        <p class="text-sm uppercase tracking-[0.3em] text-slate-500">Profile</p>
        <h2 class="text-2xl font-semibold">${state.profile.name}</h2>
        <p class="text-slate-600">Email: <span class="font-medium text-slate-900">${state.profile.email}</span></p>
        <p class="text-slate-600">User Id: <span class="font-medium text-slate-900">${state.profile.id}</span></p>
      </div>
      <div class="rounded-3xl bg-slate-950 p-5 text-white">
        <p class="text-sm uppercase tracking-[0.3em] text-slate-400">Bookings</p>
        <p class="mt-4 text-4xl font-semibold">${Array.isArray(state.profile.bookings) ? state.profile.bookings.length : '—'}</p>
        <p class="mt-2 text-sm text-slate-300">Bookings are loaded from your profile endpoint.</p>
      </div>
    </div>
  ` : '<p>Loading profile data…</p>';
    card.innerHTML = profileHtml;
    return card;
}

function renderUsersView() {
    const card = document.createElement('section');
    card.className = 'space-y-6';
    card.innerHTML = `
    <div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-2xl font-semibold">Users</h2>
          <p class="mt-2 text-sm text-slate-500">Browse all registered users and active accounts.</p>
        </div>
        <button id="refreshUsers" class="inline-flex items-center rounded-2xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700">Refresh</button>
      </div>
    </div>
    <div id="usersTable"></div>
  `;
    card.querySelector('#refreshUsers').addEventListener('click', loadUsers);
    renderUsersTable(card.querySelector('#usersTable'));
    return card;
}

function renderUsersTable(container) {
    if (!state.cached.users.length) {
        container.innerHTML = '<div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70 text-slate-500">No users loaded yet.</div>';
        return;
    }
    container.innerHTML = `
    <div class="overflow-hidden rounded-3xl bg-white/90 shadow-lg shadow-slate-200/70">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-950 text-white">
            <tr>
              <th class="px-4 py-3 text-left font-medium">ID</th>
              <th class="px-4 py-3 text-left font-medium">Name</th>
              <th class="px-4 py-3 text-left font-medium">Email</th>
              <th class="px-4 py-3 text-left font-medium">Role</th>
              <th class="px-4 py-3 text-left font-medium">Active</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 bg-white">
            ${state.cached.users.map(user => `
              <tr>
                <td class="px-4 py-4">${user.id ?? '—'}</td>
                <td class="px-4 py-4">${user.name ?? '—'}</td>
                <td class="px-4 py-4">${user.email ?? '—'}</td>
                <td class="px-4 py-4">${user.role ?? '—'}</td>
                <td class="px-4 py-4">${user.is_active ? 'Yes' : 'No'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderServicesView() {
    const card = document.createElement('section');
    card.className = 'space-y-6';
    card.innerHTML = `
    <div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-2xl font-semibold">Services</h2>
          <p class="mt-2 text-sm text-slate-500">See current services available for scheduling.</p>
        </div>
        <button id="refreshServices" class="inline-flex items-center rounded-2xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700">Refresh</button>
      </div>
    </div>
    <div id="servicesTable"></div>
  `;
    card.querySelector('#refreshServices').addEventListener('click', loadServices);
    renderServicesTable(card.querySelector('#servicesTable'));
    return card;
}

function renderServicesTable(container) {
    if (!state.cached.services.length) {
        container.innerHTML = '<div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70 text-slate-500">No services loaded yet.</div>';
        return;
    }
    container.innerHTML = `
    <div class="overflow-hidden rounded-3xl bg-white/90 shadow-lg shadow-slate-200/70">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-950 text-white">
            <tr>
              <th class="px-4 py-3 text-left font-medium">ID</th>
              <th class="px-4 py-3 text-left font-medium">Name</th>
              <th class="px-4 py-3 text-left font-medium">Duration</th>
              <th class="px-4 py-3 text-left font-medium">Capacity</th>
              <th class="px-4 py-3 text-left font-medium">Price</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 bg-white">
            ${state.cached.services.map(service => `
              <tr>
                <td class="px-4 py-4">${service.id ?? '—'}</td>
                <td class="px-4 py-4">${service.name ?? '—'}</td>
                <td class="px-4 py-4">${service.duration_minutes ? service.duration_minutes + ' min' : '—'}</td>
                <td class="px-4 py-4">${service.capacity ?? '—'}</td>
                <td class="px-4 py-4">${service.price != null ? '$' + Number(service.price).toFixed(2) : '—'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderSlotsView() {
    const card = document.createElement('section');
    card.className = 'space-y-6';
    card.innerHTML = `
    <div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-2xl font-semibold">Slots</h2>
          <p class="mt-2 text-sm text-slate-500">Review available slots across services and trainers.</p>
        </div>
        <button id="refreshSlots" class="inline-flex items-center rounded-2xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700">Refresh</button>
      </div>
    </div>
    <div id="slotsTable"></div>
  `;
    card.querySelector('#refreshSlots').addEventListener('click', loadSlots);
    renderSlotsTable(card.querySelector('#slotsTable'));
    return card;
}

function renderSlotsTable(container) {
    if (!state.cached.slots.length) {
        container.innerHTML = '<div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70 text-slate-500">No slots loaded yet.</div>';
        return;
    }
    container.innerHTML = `
    <div class="overflow-hidden rounded-3xl bg-white/90 shadow-lg shadow-slate-200/70">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-950 text-white">
            <tr>
              <th class="px-4 py-3 text-left font-medium">ID</th>
              <th class="px-4 py-3 text-left font-medium">Service</th>
              <th class="px-4 py-3 text-left font-medium">Start</th>
              <th class="px-4 py-3 text-left font-medium">End</th>
              <th class="px-4 py-3 text-left font-medium">Trainer</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 bg-white">
            ${state.cached.slots.map(slot => `
              <tr>
                <td class="px-4 py-4">${slot.id ?? '—'}</td>
                <td class="px-4 py-4">${slot.service_id ?? '—'}</td>
                <td class="px-4 py-4">${formatDate(slot.start_time)}</td>
                <td class="px-4 py-4">${formatDate(slot.end_time)}</td>
                <td class="px-4 py-4">${slot.trainer_id ?? '—'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderBookingsView() {
    const card = document.createElement('section');
    card.className = 'space-y-6';
    card.innerHTML = `
    <div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-2xl font-semibold">Bookings</h2>
          <p class="mt-2 text-sm text-slate-500">Manage reservations created by users.</p>
        </div>
        <button id="refreshBookings" class="inline-flex items-center rounded-2xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700">Refresh</button>
      </div>
    </div>
    <div id="bookingsTable"></div>
  `;
    card.querySelector('#refreshBookings').addEventListener('click', loadBookings);
    renderBookingsTable(card.querySelector('#bookingsTable'));
    return card;
}

function renderBookingsTable(container) {
    if (!state.cached.bookings.length) {
        container.innerHTML = '<div class="rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70 text-slate-500">No bookings loaded yet.</div>';
        return;
    }
    container.innerHTML = `
    <div class="overflow-hidden rounded-3xl bg-white/90 shadow-lg shadow-slate-200/70">
      <div class="overflow-x-auto scrollbar-thin">
        <table class="min-w-full divide-y divide-slate-200 text-sm">
          <thead class="bg-slate-950 text-white">
            <tr>
              <th class="px-4 py-3 text-left font-medium">Booking ID</th>
              <th class="px-4 py-3 text-left font-medium">User</th>
              <th class="px-4 py-3 text-left font-medium">Slot</th>
              <th class="px-4 py-3 text-left font-medium">Status</th>
              <th class="px-4 py-3 text-left font-medium">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 bg-white">
            ${state.cached.bookings.map(booking => `
              <tr>
                <td class="px-4 py-4">${booking.id ?? '—'}</td>
                <td class="px-4 py-4">${booking.user_id ?? '—'}</td>
                <td class="px-4 py-4">${booking.slot_id ?? '—'}</td>
                <td class="px-4 py-4">${booking.status ?? '—'}</td>
                <td class="px-4 py-4 space-x-2">
                  <button data-action="confirm" data-id="${booking.id}" class="rounded-2xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-700">Confirm</button>
                  <button data-action="cancel" data-id="${booking.id}" class="rounded-2xl bg-rose-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-rose-700">Cancel</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
    container.querySelectorAll('[data-action]').forEach(button => {
        button.addEventListener('click', async () => {
            const id = button.dataset.id;
            const action = button.dataset.action;
            if (action === 'confirm') {
                await handleBookingStateChange(id, 'confirm');
            } else {
                await handleBookingStateChange(id, 'cancel');
            }
        });
    });
}

function renderServiceForm() {
    const card = document.createElement('section');
    card.className = 'rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70';
    card.innerHTML = `
    <div class="space-y-4">
      <div>
        <h2 class="text-2xl font-semibold">Create Service</h2>
        <p class="mt-2 text-sm text-slate-500">Add a new service offering to the system.</p>
      </div>
      <form id="serviceForm" class="grid gap-4 md:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">Name<input id="serviceName" type="text" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Price<input id="servicePrice" type="number" step="0.01" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Duration (minutes)<input id="serviceDuration" type="number" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Capacity<input id="serviceCapacity" type="number" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="md:col-span-2 block text-sm font-medium text-slate-700">Description<textarea id="serviceDescription" rows="4" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"></textarea></label>
        <button class="md:col-span-2 rounded-2xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">Create Service</button>
      </form>
    </div>
  `;
    card.querySelector('#serviceForm').addEventListener('submit', handleCreateService);
    return card;
}

function renderSlotForm() {
    const card = document.createElement('section');
    card.className = 'rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70';
    card.innerHTML = `
    <div class="space-y-4">
      <div>
        <h2 class="text-2xl font-semibold">Create Slot</h2>
        <p class="mt-2 text-sm text-slate-500">Schedule a new slot for a service.</p>
      </div>
      <form id="slotForm" class="grid gap-4 md:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">Service ID<input id="slotServiceId" type="number" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Trainer ID<input id="slotTrainerId" type="number" class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Start Time<input id="slotStart" type="datetime-local" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">End Time<input id="slotEnd" type="datetime-local" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Capacity<input id="slotCapacity" type="number" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <button class="md:col-span-2 rounded-2xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">Create Slot</button>
      </form>
    </div>
  `;
    card.querySelector('#slotForm').addEventListener('submit', handleCreateSlot);
    return card;
}

function renderBookingForm() {
    const card = document.createElement('section');
    card.className = 'rounded-3xl bg-white/90 p-6 shadow-lg shadow-slate-200/70';
    card.innerHTML = `
    <div class="space-y-4">
      <div>
        <h2 class="text-2xl font-semibold">Create Booking</h2>
        <p class="mt-2 text-sm text-slate-500">Book a slot for a user.</p>
      </div>
      <form id="bookingForm" class="grid gap-4 md:grid-cols-2">
        <label class="block text-sm font-medium text-slate-700">User ID<input id="bookingUserId" type="number" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <label class="block text-sm font-medium text-slate-700">Slot ID<input id="bookingSlotId" type="number" required class="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100" /></label>
        <button class="md:col-span-2 rounded-2xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-700">Create Booking</button>
      </form>
    </div>
  `;
    card.querySelector('#bookingForm').addEventListener('submit', handleCreateBooking);
    return card;
}

async function handleCreateService(event) {
    event.preventDefault();
    const payload = {
        name: document.getElementById('serviceName').value.trim(),
        description: document.getElementById('serviceDescription').value.trim(),
        duration_minutes: Number(document.getElementById('serviceDuration').value),
        capacity: Number(document.getElementById('serviceCapacity').value),
        price: Number(document.getElementById('servicePrice').value)
    };
    try {
        await apiRequest('/services/add_service', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        setMessage('success', 'Service created successfully.');
        document.getElementById('serviceForm').reset();
        loadServices();
    } catch (error) {
        setMessage('error', `Service creation failed: ${error.message}`);
    }
}

async function handleCreateSlot(event) {
    event.preventDefault();
    const payload = {
        service_id: Number(document.getElementById('slotServiceId').value),
        start_time: document.getElementById('slotStart').value,
        end_time: document.getElementById('slotEnd').value,
        capacity: Number(document.getElementById('slotCapacity').value)
    };
    const trainerId = document.getElementById('slotTrainerId').value;
    if (trainerId) payload.trainer_id = Number(trainerId);
    try {
        await apiRequest(`/slots/create_slot${queryString(payload)}`, { method: 'POST' });
        setMessage('success', 'Slot created successfully.');
        document.getElementById('slotForm').reset();
        loadSlots();
    } catch (error) {
        setMessage('error', `Slot creation failed: ${error.message}`);
    }
}

async function handleCreateBooking(event) {
    event.preventDefault();
    const payload = {
        user_id: Number(document.getElementById('bookingUserId').value),
        slot_id: Number(document.getElementById('bookingSlotId').value)
    };
    try {
        await apiRequest(`/booking/book${queryString(payload)}`, { method: 'POST' });
        setMessage('success', 'Booking created successfully.');
        document.getElementById('bookingForm').reset();
        loadBookings();
    } catch (error) {
        setMessage('error', `Booking creation failed: ${error.message}`);
    }
}

async function handleBookingStateChange(bookingId, action) {
    try {
        await apiRequest(`/booking/${bookingId}/${action}`, { method: 'PUT' });
        setMessage('success', `Booking ${action}ed successfully.`);
        loadBookings();
    } catch (error) {
        setMessage('error', `${action.charAt(0).toUpperCase() + action.slice(1)} failed: ${error.message}`);
    }
}

async function loadProfile() {
    try {
        state.profile = await apiRequest('/auth/about');
        renderMainSection();
    } catch (error) {
        setMessage('error', `Unable to load profile: ${error.message}`);
    }
}

async function loadUsers() {
    try {
        const data = await apiRequest('/users/' + queryString({ page: 1, size: 20 }));
        state.cached.users = Array.isArray(data) ? data : data.results || [];
        if (state.activeTab === 'users') renderMainSection();
    } catch (error) {
        setMessage('error', `Unable to load users: ${error.message}`);
    }
}

async function loadServices() {
    try {
        const data = await apiRequest('/services/' + queryString({ page: 1, size: 50 }));
        state.cached.services = Array.isArray(data) ? data : data.results || [];
        if (state.activeTab === 'services') renderMainSection();
    } catch (error) {
        setMessage('error', `Unable to load services: ${error.message}`);
    }
}

async function loadSlots() {
    try {
        const data = await apiRequest('/slots/get_slots');
        state.cached.slots = Array.isArray(data) ? data : data.results || [];
        if (state.activeTab === 'slots') renderMainSection();
    } catch (error) {
        setMessage('error', `Unable to load slots: ${error.message}`);
    }
}

async function loadBookings() {
    try {
        const data = await apiRequest('/booking/bookings');
        state.cached.bookings = Array.isArray(data) ? data : data.results || [];
        if (state.activeTab === 'bookings') renderMainSection();
    } catch (error) {
        setMessage('error', `Unable to load bookings: ${error.message}`);
    }
}

function handleLogout() {
    state.token = null;
    state.tokenType = 'bearer';
    state.profile = null;
    localStorage.removeItem('gym_token');
    localStorage.removeItem('gym_token_type');
    setMessage('info', 'Logged out successfully.');
    renderAuthView();
}

function formatDate(value) {
    if (!value) return '—';
    try {
        const date = new Date(value);
        return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
    } catch {
        return value;
    }
}
