import React, { useEffect, useRef, useState, useCallback } from 'react';
import { usePopper } from 'react-popper';

// --- Utility Functions (Date Handling) ---
const toISO = (d) => {
  if (!d || isNaN(d)) return '';
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const parseISO = (s) => {
  if (!s) return null;
  const [y, m, d] = s.split('-').map(Number);
  if (y < 1000 || m < 1 || m > 12 || d < 1 || d > 31) return null;
  return new Date(y, m - 1, d);
};

const getDaysInMonth = (date) => new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
const getFirstDayDayOfWeek = (date) => new Date(date.getFullYear(), date.getMonth(), 1).getDay(); // 0 (Sun) to 6 (Sat)
const isSameDay = (d1, d2) => d1 && d2 && toISO(d1) === toISO(d2);
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const getStartYearOfDecade = (date) => date.getFullYear() - (date.getFullYear() % 10);

// --- Main Component ---
const DatePicker = ({ label, value, onChange, minDate, required = false, disabled = false, placeholder = 'Select Date' }) => {
  const [open, setOpen] = useState(false);
  const initialDate = parseISO(value) || new Date();
  const [visDate, setVisDate] = useState(initialDate);
  const [view, setView] = useState('days'); // 'days', 'months', 'years'
  
  const containerRef = useRef(null);
  const [referenceElement, setReferenceElement] = useState(null);
  const [popperElement, setPopperElement] = useState(null);

  const { styles, attributes } = usePopper(referenceElement, popperElement, {
    placement: 'bottom-start',
    modifiers: [
      { name: 'offset', options: { offset: [0, 8] } },
      { name: 'flip', options: { fallbackPlacements: ['bottom-end', 'top-start', 'top-end'] } },
    ],
  });

  // --- Effects ---
  useEffect(() => {
    const handle = (e) => {
      if (popperElement && referenceElement && !popperElement.contains(e.target) && !referenceElement.contains(e.target)) {
        setOpen(false);
      }
    };
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handle);
    document.addEventListener('touchstart', handle);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', handle);
      document.removeEventListener('touchstart', handle);
      document.removeEventListener('keydown', onKey);
    };
  }, [popperElement, referenceElement]);

  // Reset view to 'days' when picker is closed or value changes
  useEffect(() => {
    if (!open) {
      setView('days');
    }
  }, [open]);

  useEffect(() => {
    const parsed = parseISO(value);
    if (parsed && !isSameDay(visDate, parsed)) {
      setVisDate(parsed);
    }
  }, [value]);

  // --- Navigation Handlers ---
  const changeDate = (delta, unit) => {
    setVisDate(prevDate => {
      const d = new Date(prevDate);
      if (unit === 'month') {
        d.setDate(1);
        d.setMonth(d.getMonth() + delta);
      } else if (unit === 'year') {
        d.setFullYear(d.getFullYear() + delta);
      } else if (unit === 'decade') { // For year grid navigation
        d.setFullYear(d.getFullYear() + (delta * 10));
      }
      return d;
    });
  };

  const isBeforeMin = useCallback((d) => {
    if (!minDate) return false;
    const min = parseISO(minDate);
    if (!min) return false;
    return toISO(d) < toISO(min);
  }, [minDate]);

  // --- Selection Handlers ---
  const handleDaySelect = (d) => {
    if (disabled || isBeforeMin(d)) return;
    const iso = toISO(d);
    if (onChange) {
      onChange({ target: { value: iso } });
    }
    setOpen(false);
  };

  const handleMonthSelect = (monthIndex) => {
    setVisDate(prevDate => {
      const d = new Date(prevDate);
      d.setMonth(monthIndex);
      return d;
    });
    setView('days'); // Go back to day view
  };

  const handleYearSelect = (year) => {
    setVisDate(prevDate => {
      const d = new Date(prevDate);
      d.setFullYear(year);
      return d;
    });
    setView('months'); // Go back to month view
  };

  // --- Render Functions for Grids ---
  const renderDayGrid = () => {
    const days = [];
    const daysInMonth = getDaysInMonth(visDate);
    const firstDay = getFirstDayDayOfWeek(visDate);
    const today = new Date();
    const selectedDate = parseISO(value);

    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="w-7 h-7" />);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(visDate.getFullYear(), visDate.getMonth(), day);
      const isSelected = isSameDay(selectedDate, date);
      const isToday = isSameDay(today, date);
      const disabledDay = isBeforeMin(date) || disabled;

      let buttonClass = 'text-gray-700 hover:bg-gray-100';
      if (disabledDay) buttonClass = 'text-gray-300 cursor-not-allowed';
      else if (isSelected) buttonClass = 'bg-blue-500 text-white font-semibold shadow-sm';
      else if (isToday) buttonClass = 'text-blue-500 font-semibold border border-blue-500/50 hover:bg-blue-500/10';
      else buttonClass = 'text-gray-700 hover:bg-gray-100';
      
      days.push(
        <button
          key={day}
          onClick={() => handleDaySelect(date)}
          className={`w-7 h-7 text-sm flex items-center justify-center rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 ${buttonClass}`}
          aria-pressed={isSelected}
          disabled={disabledDay}
        >
          {day}
        </button>
      );
    }
    return days;
  };

  const renderMonthGrid = () => {
    const selectedYear = visDate.getFullYear();
    return MONTH_NAMES.map((month, index) => {
      const isCurrentMonth = selectedYear === new Date().getFullYear() && index === new Date().getMonth();
      const isSelectedMonth = selectedYear === (parseISO(value)?.getFullYear()) && index === (parseISO(value)?.getMonth());

      let buttonClass = 'text-gray-700 hover:bg-gray-100';
      if (isSelectedMonth) buttonClass = 'bg-blue-500 text-white font-semibold shadow-sm';
      else if (isCurrentMonth) buttonClass = 'text-blue-500 font-semibold border border-blue-500/50 hover:bg-blue-500/10';

      return (
        <button
          key={month}
          onClick={() => handleMonthSelect(index)}
          className={`w-1/3 h-10 text-sm flex items-center justify-center rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 ${buttonClass}`}
        >
          {month}
        </button>
      );
    });
  };

  // Reverted to a grid-based year selection
  const renderYearGrid = () => {
    const startYear = getStartYearOfDecade(visDate);
    const yearsInDecade = [];
    for (let i = 0; i < 10; i++) { // Current decade
        yearsInDecade.push(startYear + i);
    }

    // Add previous and next year for padding, similar to original mock for month view
    const allYears = [startYear - 1, ...yearsInDecade, startYear + 10];
    
    const selectedYear = parseISO(value)?.getFullYear();
    const currentFullYear = new Date().getFullYear();

    return allYears.map((year, index) => {
      // Style first and last year in the `allYears` array as grayed out padding
      const isPaddingYear = index === 0 || index === allYears.length - 1; 

      const isCurrentYear = year === currentFullYear;
      const isSelectedYear = year === selectedYear;
      
      let buttonClass = 'text-gray-700 hover:bg-gray-100';
      if (isPaddingYear) buttonClass = 'text-gray-300'; // Gray out padding years
      else if (isSelectedYear) buttonClass = 'bg-blue-500 text-white font-semibold shadow-sm';
      else if (isCurrentYear) buttonClass = 'text-blue-500 font-semibold border border-blue-500/50 hover:bg-blue-500/10';

      return (
        <button
          key={year}
          onClick={() => handleYearSelect(year)}
          className={`w-1/4 h-10 text-sm flex items-center justify-center rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 ${buttonClass}`}
          disabled={isPaddingYear} // Disable interaction for padding years
        >
          {year}
        </button>
      );
    });
  };

  // --- Main Render ---
  const displayInputLabel = label ? (
    <label className="custom-label">{label} {required && <span className="text-red-500">*</span>}</label>
  ) : null;

  const formattedDisplay = (val) => {
    const d = parseISO(val);
    if (!d) return '';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const renderHeader = () => {
    let headerText = '';
    let onHeaderClick = () => {};
    let onPrevClick = () => {};
    let onNextClick = () => {};
    let showNavArrows = true;
    let showChevron = true;

    if (view === 'days') {
      headerText = visDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      onHeaderClick = () => setView('months');
      onPrevClick = () => changeDate(-1, 'month');
      onNextClick = () => changeDate(1, 'month');
    } else if (view === 'months') {
      headerText = visDate.getFullYear().toString();
      onHeaderClick = () => setView('years');
      onPrevClick = () => changeDate(-1, 'year');
      onNextClick = () => changeDate(1, 'year');
    } else { // view === 'years'
      const startYear = getStartYearOfDecade(visDate);
      headerText = `${startYear} - ${startYear + 9}`;
      onHeaderClick = () => {}; // No action for decade header click
      onPrevClick = () => changeDate(-1, 'decade');
      onNextClick = () => changeDate(1, 'decade');
      showChevron = false; // No chevron for decade view
    }

    return (
      <div className="flex flex-col p-2 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <button
            type="button"
            className="font-semibold text-base text-medical-dark flex items-center p-0.5 rounded-lg hover:bg-gray-100"
            onClick={onHeaderClick}
            disabled={view === 'years' && onHeaderClick === null} // Disable if year range and no click action
          >
            {headerText}
            {showChevron && (
              <svg className="w-3 h-3 ml-1 text-medical-gray" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
          
          <div className="flex items-center space-x-1">
            {showNavArrows && (
              <>
                <button
                  type="button"
                  onClick={onPrevClick}
                  className="p-1 rounded-full hover:bg-gray-100 transition-colors text-medical-dark"
                  title="Previous"
                >
                  <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={onNextClick}
                  className="p-1 rounded-full hover:bg-gray-100 transition-colors text-medical-dark"
                  title="Next"
                >
                  <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderBody = () => {
    if (view === 'days') {
      return (
        <div className="p-2">
          <div className="grid grid-cols-7 gap-0 text-center text-xs font-medium text-medical-gray mb-1">
            {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(d => <div key={d} className="text-gray-500 text-xs font-medium">{d}</div>)}
          </div>
          <div className="grid grid-cols-7 gap-0 justify-items-center">
            {renderDayGrid()}
          </div>
        </div>
      );
    }
    if (view === 'months') {
      return (
        <div className="p-2 grid grid-cols-3 gap-1 justify-items-center"> {/* Changed to grid for months */}
          {renderMonthGrid()}
        </div>
      );
    }
    if (view === 'years') {
      return (
        // Changed to grid for years, removed space-y-1 and flex-col
        <div className="p-2 grid grid-cols-4 gap-1 justify-items-center">
          {renderYearGrid()}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="relative inline-block w-full" ref={containerRef}>
      {displayInputLabel}
      <div ref={setReferenceElement}>
        <button
          type="button"
          onClick={() => { if (!disabled) setOpen((s) => !s); }}
          className={`form-input-themed custom-datetime flex items-center justify-between w-full text-left transition-shadow ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'hover:shadow-md'}`}
          aria-haspopup="dialog"
          aria-expanded={open}
          disabled={disabled}
        >
          <span className={`${value ? 'text-medical-dark' : 'text-medical-gray'}`}>{value ? formattedDisplay(value) : placeholder}</span>
          <svg className="w-4 h-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
            <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4Zm-2 13H4V8h14v9Z"/>
          </svg>
        </button>
      </div>

      {open && (
        <div 
          ref={popperElement} // Note: Directly using popperElement now that scrollBodyRef is gone
          style={{ ...styles.popper, minWidth: '240px' }}
          {...attributes.popper}
          className="z-50 bg-white rounded-xl shadow-2xl border border-gray-200 transition-opacity duration-150 h-80 flex flex-col" 
          role="dialog" 
          aria-modal="true"
        >
          {renderHeader()}
          <div className="flex-1 overflow-y-auto"> {/* Removed scrollBodyRef as it's no longer needed for year scrolling */}
            {renderBody()}
          </div>
        </div>
      )}
    </div>
  );
};

export default DatePicker;