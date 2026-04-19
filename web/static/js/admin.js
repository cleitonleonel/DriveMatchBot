/**
 * DriveMatch Admin Panel - Main Logic
 */

// Initialize Icons
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ DriveMatch Admin JS Loaded');
    if (window.lucide) {
        lucide.createIcons();
    }
});

/**
 * Dashboard Logic
 */
async function initDashboard(stats) {
    try {
        const response = await fetch('/api/metrics');
        if (!response.ok) throw new Error('Failed to fetch metrics');
        const metrics = await response.json();
        
        const revCtx = document.getElementById('revenueChart');
        if (revCtx) {
            new Chart(revCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: metrics.map(m => m.date),
                    datasets: [{
                        label: 'Receita Total (R$)',
                        data: metrics.map(m => m.total),
                        borderColor: '#8b5cf6',
                        tension: 0.4,
                        fill: true,
                        backgroundColor: 'rgba(139, 92, 246, 0.1)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        const userCtx = document.getElementById('usersChart');
        if (userCtx) {
            new Chart(userCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Motoristas', 'Passageiros'],
                    datasets: [{
                        data: [stats.drivers_count, stats.users_count - stats.drivers_count],
                        backgroundColor: ['#8b5cf6', '#1e293b'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }
    } catch (error) {
        console.error('Error loading dashboard metrics:', error);
    }
}

/**
 * User Management
 */
async function toggleUser(userId) {
    const badge = document.getElementById(`status-${userId}`);
    const originalText = badge.innerText;
    
    try {
        badge.innerText = '...';
        const response = await fetch(`/api/users/${userId}/toggle`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            badge.className = `status-badge ${data.is_active ? 'status-active' : 'status-inactive'}`;
            badge.innerText = data.is_active ? 'Ativo' : 'Inativo';
        } else {
            badge.innerText = originalText;
        }
    } catch (error) {
        console.error('Error toggling user status:', error);
        badge.innerText = originalText;
        alert('Falha ao atualizar usuário.');
    }
}

/**
 * Payout Management
 */
async function confirmPayout(requestId) {
    if (!confirm('Você confirma que já realizou o PIX para este motorista?')) return;
    
    const row = document.getElementById(`payout-row-${requestId}`);
    const btn = row.querySelector('button');
    const originalBtnText = btn.innerHTML;

    try {
        btn.disabled = true;
        btn.innerText = 'Processando...';
        
        const response = await fetch(`/api/payouts/${requestId}/confirm`, { method: 'POST' });
        if (response.ok) {
            alert('Pagamento confirmado com sucesso!');
            if (row) row.remove();
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        console.error('Error confirming payout:', error);
        btn.disabled = false;
        btn.innerHTML = originalBtnText;
        alert('Falha ao confirmar pagamento.');
    }
}

/**
 * Settings Management
 */
async function initSettings() {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    console.log('⚙️ Initializing Settings Page');

    const btn = form.querySelector('button[type="submit"]');

    // Load initial data
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const settings = await response.json();
            for (const key in settings) {
                const input = document.getElementById(key);
                if (input) input.value = settings[key];
            }
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }

    // Handle Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('💾 Saving settings...');
        
        const originalBtnText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Salvando...';
        lucide.createIcons(); // Update icons for the loader

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const res = await fetch('/api/settings', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                alert('Configurações atualizadas com sucesso!');
            } else {
                throw new Error('Update failed');
            }
        } catch (err) {
            console.error('Update error:', err);
            alert('Erro ao salvar configurações.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalBtnText;
            lucide.createIcons();
        }
    });
}

/**
 * UI Utilities
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}
