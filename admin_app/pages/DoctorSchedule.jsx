const DoctorSchedule = ({ openModal, closeModal, user }) => {
    const [schedules, setSchedules] = React.useState({ 1: {}, 2: {} });
    const [locations, setLocations] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [showModal, setShowModal] = React.useState(false);
    const [modalContent, setModalContent] = React.useState(null);
    const [currentDate, setCurrentDate] = React.useState(new Date());
    const [unavailablePeriods, setUnavailablePeriods] = React.useState({ 1: [], 2: [] });
    const [modalTitle, setModalTitle] = React.useState('');

    const fetchSchedulesAndLocations = async () => {
        setLoading(true);
        try {
            const fetchedLocations = [
                { id: 1, name: "Home Clinic" },
                { id: 2, name: "Hospital" }
            ];
            setLocations(fetchedLocations);

            const newSchedules = { 1: {}, 2: {} };
            for (const loc of fetchedLocations) {
                const data = await window.api(`/api/v1/schedules/by-location/${loc.id}`);
                const scheduleMap = (data || []).reduce((acc, item) => {
                    acc[item.day_of_week] = item;
                    return acc;
                }, {});
                newSchedules[loc.id] = scheduleMap;
            }
            setSchedules(newSchedules);
        } catch (error) {
            console.error("Error fetching schedules:", error);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchSchedulesAndLocations();
    }, []);

    React.useEffect(() => {
        const fetchUnavailablePeriods = async () => {
            const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

            const toISODate = (d) => d.toISOString().split('T')[0];
            const startDate = toISODate(firstDay);
            const endDate = toISODate(lastDay);

            try {
                const [clinicPeriods, hospitalPeriods] = await Promise.all([
                    window.api(`/api/v1/unavailable-periods/1?start_date=${startDate}&end_date=${endDate}`),
                    window.api(`/api/v1/unavailable-periods/2?start_date=${startDate}&end_date=${endDate}`)
                ]);

                setUnavailablePeriods({
                    1: Array.isArray(clinicPeriods) ? clinicPeriods : [],
                    2: Array.isArray(hospitalPeriods) ? hospitalPeriods : []
                });
            } catch (error) {
                console.error("Error fetching unavailable periods:", error);
                setUnavailablePeriods({ 1: [], 2: [] });
            }
        };

        fetchUnavailablePeriods();
    }, [currentDate]);

    const handleModalCloseAndRefresh = () => {
        setShowModal(false);
        setCurrentDate(new Date(currentDate.getTime()));
        fetchSchedulesAndLocations();
    };

    const handleDateClick = (date, scheduleForDay) => {
        setModalTitle(`Edit Day: ${date.toLocaleDateString()}`);

        const findBlockForDate = (periods, clickedDate) => {
            if (!periods) return null;
            const checkDate = new Date(clickedDate.getFullYear(), clickedDate.getMonth(), clickedDate.getDate());

            for (const period of periods) {
                const periodStartDate = new Date(period.start_datetime);
                const periodEndDate = new Date(period.end_datetime);
                const startDateOnly = new Date(periodStartDate.getFullYear(), periodStartDate.getMonth(), periodStartDate.getDate());
                const endDateOnly = new Date(periodEndDate.getFullYear(), periodEndDate.getMonth(), periodEndDate.getDate());

                if (checkDate >= startDateOnly && checkDate <= endDateOnly) {
                    return period;
                }
            }
            return null;
        };

        const existingClinicBlock = findBlockForDate(unavailablePeriods[1], date);
        const existingHospitalBlock = findBlockForDate(unavailablePeriods[2], date);

        setModalContent(
            <DayEditorModal
                date={date}
                scheduleForDay={scheduleForDay}
                onClose={handleModalCloseAndRefresh}
                refreshSchedules={fetchSchedulesAndLocations}
                existingClinicBlock={existingClinicBlock}
                existingHospitalBlock={existingHospitalBlock}
            />
        );
        setShowModal(true);
    };

    if (loading) return <LoadingSpinner />;

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark font-primary">Doctor Schedule</h2>
                {user?.permissions?.can_edit_schedule && (
                    <div className="flex space-x-2 sm:space-x-4">
                        <button
                            onClick={() => {
                                setModalTitle('Emergency Day Block');
                                setModalContent(<EmergencyBlockModal onClose={handleModalCloseAndRefresh} />);
                                setShowModal(true);
                            }}
                            className="bg-red-600 hover:bg-red-700 px-6 py-3 text-white rounded-xl font-secondary flex flex-wrap items-center gap-2 relative z-10 transition-all duration-300 transform hover:scale-105"
                        >
                            <i className="fas fa-exclamation-triangle"></i>
                            <span>Emergency Block</span>
                        </button>
                        <button
                            onClick={() => {
                                setModalTitle('Edit Weekly Schedule');
                                setModalContent(<ScheduleEditor schedules={schedules} locations={locations} onSaveSuccess={fetchSchedulesAndLocations} onClose={handleModalCloseAndRefresh} />);
                                setShowModal(true);
                            }}
                            className="medical-button px-6 py-3 text-white rounded-xl font-secondary flex flex-wrap items-center gap-2 relative z-10"
                        >
                            <i className="fas fa-edit"></i>
                            <span>Edit Weekly Schedule</span>
                        </button>
                    </div>
                )}
            </div>

            <ScheduleCalendar
                homeClinicSchedule={schedules[1]}
                hospitalSchedule={schedules[2]}
                onDateClick={handleDateClick}
                currentDate={currentDate}
                setCurrentDate={setCurrentDate}
                unavailablePeriods={unavailablePeriods}
            />

            <Modal
                isOpen={showModal}
                onClose={handleModalCloseAndRefresh}
                title={modalTitle}
                width="max-w-4xl"
            >
                {modalContent}
            </Modal>
        </div>
    );
};

window.DoctorSchedule = DoctorSchedule;

