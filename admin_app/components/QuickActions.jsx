const QuickActions = () => {
    const [open, setOpen] = React.useState(false);
    const [services, setServices] = React.useState(null);
    const [config, setConfig] = React.useState({ appointment_interval_minutes: 15, appointment_daily_limit: 2 });
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState("");

    const fetchServices = async () => {
        setLoading(true); setError("");
        try {
            const data = await api('/api/v1/services/status');
            setServices(data);
        } catch (e) { setError('Failed to load services status'); }
        finally { setLoading(false); }
    };

    const fetchConfig = async () => {
        try {
            const data = await api('/api/v1/schedules/config');
            setConfig(data);
        } catch (e) { }
    };

    React.useEffect(() => { fetchConfig(); }, []);

    const saveConfig = async () => {
        setLoading(true); setError("");
        try {
            await api(`/api/v1/schedules/config?appointment_interval_minutes=${config.appointment_interval_minutes}&appointment_daily_limit=${config.appointment_daily_limit}`, { method: 'POST' });
            toast('Schedule config saved');
        } catch (e) { setError('Failed to save config'); }
        finally { setLoading(false); }
    };

    const onTemplateUpload = async (e) => {
        const file = e.target.files?.[0]; if (!file) return;
        const token = sessionStorage.getItem('accessToken');
        const form = new FormData(); form.append('template_file', file);
        try {
                    const res = await fetch(window.API_BASE_URL + '/api/v1/prescriptions/template/upload', {
                method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: form
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.detail || 'Upload failed');
            toast('Template uploaded');
        } catch (err) { toast('Template upload failed'); }
    };

    const onHandwrittenUpload = async (patientId, file) => {
        if (!file || !patientId) return toast('Select patient and file');
        const token = sessionStorage.getItem('accessToken');
        const form = new FormData(); form.append('patient_id', String(patientId)); form.append('file', file);
        try {
                    const res = await fetch(window.API_BASE_URL + '/api/v1/prescriptions/handwritten/upload', {
                method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: form
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.detail || 'Upload failed');
            toast('Handwritten prescription uploaded');
        } catch (err) { toast('Upload failed'); }
    };

    const [editorHtml, setEditorHtml] = React.useState('');
    const [editorPatientId, setEditorPatientId] = React.useState('');
    const saveEditor = async () => {
        if (!editorHtml || !editorPatientId) return toast('Enter patient and content');
        const token = sessionStorage.getItem('accessToken');
        const form = new FormData(); form.append('patient_id', editorPatientId); form.append('html_content', editorHtml);
        try {
                    const res = await fetch(window.API_BASE_URL + '/api/v1/prescriptions/editor/save', {
                method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: form
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.detail || 'Save failed');
            toast('Prescription saved');
        } catch (err) { toast('Save failed'); }
    };

    return (
        <>
            <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-3">
                {open && (
                    <div className="medical-card p-4 rounded-xl w-96 shadow-xl">
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="font-semibold text-medical-dark">Quick Actions</h3>
                            <button onClick={() => setOpen(false)} className="text-medical-gray"><i className="fas fa-times"></i></button>
                        </div>
                        {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
                        <div className="space-y-4">
                            <div className="border-b pb-3">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-medium">Services status</span>
                                    <button onClick={fetchServices} className="text-medical-accent text-sm">Refresh</button>
                                </div>
                                {loading && <LoadingSpinner />}
                                {services && (
                                    <div className="grid grid-cols-3 gap-2 text-sm">
                                        {['whatsapp', 'email', 'calendar'].map(k => (
                                            <div key={k} className="p-2 rounded bg-gray-50">
                                                <div className="capitalize">{k}</div>
                                                <div className={services[k]?.enabled ? 'text-green-600' : 'text-gray-500'}>
                                                    {services[k]?.status || (services[k]?.enabled ? 'healthy' : 'disabled')}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="border-b pb-3">
                                <div className="font-medium mb-2">Schedule config</div>
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                    <label className="text-sm w-40">Interval (min)</label>
                                    <input type="number" value={config.appointment_interval_minutes}
                                        onChange={e => setConfig({ ...config, appointment_interval_minutes: Number(e.target.value) })}
                                        className="form-input-themed" />
                                </div>
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                    <label className="text-sm w-40">Daily limit</label>
                                    <input type="number" value={config.appointment_daily_limit}
                                        onChange={e => setConfig({ ...config, appointment_daily_limit: Number(e.target.value) })}
                                        className="form-input-themed" />
                                </div>
                                <button onClick={saveConfig} className="medical-button text-white px-4 py-2 rounded">Save Config</button>
                            </div>

                            <div className="border-b pb-3">
                                <div className="font-medium mb-2">Prescription template</div>
                                <input type="file" accept="image/*,application/pdf" onChange={onTemplateUpload} className="custom-input " />
                            </div>

                            <div className="border-b pb-3">
                                <div className="font-medium mb-2">Handwritten prescription upload</div>
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                    <input type="number" placeholder="Patient ID" className="form-input-themed" id="handw_pid" />
                                </div>
                                <input type="file" accept="image/*,application/pdf" onChange={(e) => {
                                    const pid = document.getElementById('handw_pid').value;
                                    onHandwrittenUpload(pid, e.target.files?.[0]);
                                }} className="w-full" />
                            </div>
                            <div>
                                <div className="font-medium mb-2">Prescription editor save</div>
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                    <input type="number" placeholder="Patient ID" value={editorPatientId} onChange={(e) => setEditorPatientId(e.target.value)} className="form-input-themed" />
                                </div>
                                <textarea rows="4" placeholder="Paste editor HTML here" value={editorHtml} onChange={(e) => setEditorHtml(e.target.value)} className="custom-textarea"></textarea>
                                <div className="mt-2 flex justify-end">
                                    <button onClick={saveEditor} className="medical-button text-white px-4 py-2 rounded">Save</button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                <button onClick={() => setOpen(!open)} className="medical-button text-white px-4 py-3 rounded-full shadow-lg">
                    <i className="fas fa-bolt mr-2"></i>Quick Actions
                </button>
            </div>
        </>
    );
}

window.QuickActions = QuickActions;