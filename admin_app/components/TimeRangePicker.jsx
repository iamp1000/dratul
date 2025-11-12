const TimeRangePicker = ({ isOpen, onClose, onConfirm, initialStartTime, initialEndTime }) => {
  const startHourRef = React.useRef(null);
  const startMinRef = React.useRef(null);
  const endHourRef = React.useRef(null);
  const endMinRef = React.useRef(null);

  const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, "0"));
  const minutes = Array.from({ length: 12 }, (_, i) => (i * 5).toString().padStart(2, "0"));

  React.useEffect(() => {
    if (isOpen && startHourRef.current && startMinRef.current && endHourRef.current && endMinRef.current) {
      try {
        const [startH, startM] = (initialStartTime || "09:00").split(":");
        const startHourIndex = Math.max(0, hours.indexOf(startH));
        const startMinuteIndex = Math.max(0, minutes.indexOf(startM?.substring(0, 2)));
        startHourRef.current.scrollTop = startHourIndex * 44;
        startMinRef.current.scrollTop = startMinuteIndex * 44;

        const [endH, endM] = (initialEndTime || "17:00").split(":");
        const endHourIndex = Math.max(0, hours.indexOf(endH));
        const endMinuteIndex = Math.max(0, minutes.indexOf(endM?.substring(0, 2)));
        endHourRef.current.scrollTop = endHourIndex * 44;
        endMinRef.current.scrollTop = endMinuteIndex * 44;
      } catch (e) {
        console.error("Error setting initial time:", e);
      }
    }
  }, [isOpen, initialStartTime, initialEndTime]);

  const handleConfirm = () => {
    const startHourIndex = Math.round(startHourRef.current.scrollTop / 44);
    const startHour = hours[startHourIndex] || "00";
    const startMinuteIndex = Math.round(startMinRef.current.scrollTop / 44);
    const startMinute = minutes[startMinuteIndex] || "00";

    const endHourIndex = Math.round(endHourRef.current.scrollTop / 44);
    const endHour = hours[endHourIndex] || "00";
    const endMinuteIndex = Math.round(endMinRef.current.scrollTop / 44);
    const endMinute = minutes[endMinuteIndex] || "00";

    onConfirm({ startTime: `${startHour}:${startMinute}`, endTime: `${endHour}:${endMinute}` });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center modal-overlay" onClick={onClose}>
      <div className="w-auto mx-auto p-6 rounded-2xl bg-white shadow-lg border border-gray-200 text-medical-dark" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-center text-xl font-bold text-medical-dark mb-4">Pick Time Range</h2>
        <div className="flex justify-around gap-6">
          <div>
            <label className="text-center block font-semibold text-medical-accent mb-2">Start Time</label>
            <div className="flex justify-center gap-4">
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar" ref={startHourRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {hours.map((h) => (
                    <div key={`start-h-${h}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
                      {h}
                    </div>
                  ))}
                </div>
              </div>
              <span className="text-3xl font-thin text-medical-gray/70 pt-16">:</span>
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar" ref={startMinRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {minutes.map((m) => (
                    <div key={`start-m-${m}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
                      {m}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div>
            <label className="text-center block font-semibold text-medical-accent mb-2">End Time</label>
            <div className="flex justify-center gap-4">
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar" ref={endHourRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {hours.map((h) => (
                    <div key={`end-h-${h}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
                      {h}
                    </div>
                  ))}
                </div>
              </div>
              <span className="text-3xl font-thin text-medical-gray/70 pt-16">:</span>
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar" ref={endMinRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {minutes.map((m) => (
                    <div key={`end-m-${m}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
                      {m}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="px-4 py-2 bg-gray-100 text-medical-gray rounded-lg hover:bg-gray-200">
            Cancel
          </button>
          <button onClick={handleConfirm} className="medical-button px-4 py-2 text-white rounded-lg relative z-10">
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
};


