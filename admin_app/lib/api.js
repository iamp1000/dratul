const API_BASE_URL = 'http://127.0.0.1:8000';

const api = async (url, options = {}) => {
    const token = sessionStorage.getItem('accessToken');
    if (!token) {
        window.location.reload(); // Reloads app, triggering App.jsx to show LoginPage
        return;
    }

    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        }
    };

    try {
        const res = await fetch(API_BASE_URL + url, config);
        if (res.status === 401) {
            sessionStorage.clear();
            window.location.reload();
            return;
        }
        const text = await res.text();
        let data = null;
        try { data = text ? JSON.parse(text) : null; } catch { }
        if (!res.ok) {

            let errorString = 'Request failed';
            if (data) {
                if (data.detail) {

                    if (Array.isArray(data.detail)) {

                        errorString = data.detail.map(err => {
                            const loc = err.loc?.join('->') || 'field';
                            const msg = (typeof err.msg === 'string') ? err.msg : JSON.stringify(err.msg);
                            return `${loc}: ${msg}`;
                        }).join(', ');
                    } else if (typeof data.detail === 'string') {

                        errorString = data.detail;
                    } else {

                        errorString = JSON.stringify(data.detail);
                    }
                } else if (Array.isArray(data)) {

                    errorString = data.map(err => (typeof err === 'string') ? err : JSON.stringify(err)).join(', ');
                } else if (data.message) {

                    errorString = data.message;
                } else {

                    errorString = JSON.stringify(data);
                }
            } else {

                errorString = text;
            }
            throw new Error(errorString);

        }
        return data;
    } catch (error) {

        console.error('API Error (parsed):', error.message);
        console.error('Full Error Object:', error);

        throw error;
    }
};

window.API_BASE_URL = API_BASE_URL;
window.api = api;


