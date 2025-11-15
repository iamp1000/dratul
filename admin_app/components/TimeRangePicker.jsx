import React from 'react';

const TimeRangePicker = ({ isOpen, onClose, onConfirm, initialStartTime, initialEndTime }) => {
  const startHourRef = React.useRef(null);
  const startMinRef = React.useRef(null);
  const endHourRef = React.useRef(null);
  const endMinRef = React.useRef(null);

  const hoursList = React.useMemo(() => Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, "0")), []);
  const minutesList = React.useMemo(() => Array.from({ length: 12 }, (_, i) => (i * 5).toString().padStart(2, "0")), []);

  // Create long, "infinite" lists by repeating the base lists
  const hours = React.useMemo(() => Array.from({ length: 10 }).flatMap(() => hoursList), [hoursList]);
  const minutes = React.useMemo(() => Array.from({ length: 20 }).flatMap(() => minutesList), [minutesList]);

  React.useEffect(() => {
    if (isOpen && startHourRef.current && startMinRef.current && endHourRef.current && endMinRef.current) {
      // Defer scrolling to the next frame to prevent render blocking
      requestAnimationFrame(() => {
        try {
          // Set to the middle of the "infinite" list
          const startHourMidpoint = hoursList.length * 5; // 24 * 5 = 120
          const startMinuteMidpoint = minutesList.length * 10; // 12 * 10 = 120

          const [startH, startM] = (initialStartTime || "09:00").split(":");
          const startHourIndex = Math.max(0, hoursList.indexOf(startH)) + startHourMidpoint;
          const startMinuteIndex = Math.max(0, minutesList.indexOf(startM?.substring(0, 2))) + startMinuteMidpoint;
          
          // Use scrollTop for direct manipulation
          startHourRef.current.scrollTop = startHourIndex * 44;
          startMinRef.current.scrollTop = startMinuteIndex * 44;

          const [endH, endM] = (initialEndTime || "17:00").split(":");
          const endHourIndex = Math.max(0, hoursList.indexOf(endH)) + startHourMidpoint;
          const endMinuteIndex = Math.max(0, minutesList.indexOf(endM?.substring(0, 2))) + startMinuteMidpoint;
          
          endHourRef.current.scrollTop = endHourIndex * 44;
          endMinRef.current.scrollTop = endMinuteIndex * 44;
        } catch (e) {
          console.error("Error setting initial time:", e);
        }
      });
    }
  }, [isOpen, initialStartTime, initialEndTime, hoursList, minutesList]);

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
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar overscroll-contain" ref={startHourRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {hours.map((h, index) => (
                    <div key={`start-h-${h}-${index}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
                      {h}
                    </div>
                  ))}
                </div>
              </div>
              <span className="text-3xl font-thin text-medical-gray/70 pt-16">:</span>
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar overscroll-contain" ref={startMinRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {minutes.map((m, index) => (
                    <div key={`start-m-${m}-${index}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
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
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar overscroll-contain" ref={endHourRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {hours.map((h, index) => (
                    <div key={`end-h-${h}-${index}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
                      {h}
                    </div>
                  ))}
                </div>
              </div>
              <span className="text-3xl font-thin text-medical-gray/70 pt-16">:</span>
              <div className="relative h-40 w-16 overflow-y-scroll scroll-smooth snap-y snap-mandatory hide-scrollbar overscroll-contain" ref={endMinRef}>
                <div className="absolute top-1/2 left-0 right-0 h-9 bg-medical-accent/10 rounded-md -translate-y-1/2 pointer-events-none"></div>
                <div className="flex flex-col items-center text-lg font-medium space-y-2 pt-16 pb-16">
                  {minutes.map((m, index) => (
                    <div key={`end-m-${m}-${index}`} className="snap-center h-9 leading-9 text-medical-gray cursor-pointer hover:text-medical-dark">
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


export default TimeRangePicker;