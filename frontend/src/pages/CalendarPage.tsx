import React, { useContext } from 'react';
import TrainingCalendar from '../components/TrainingCalendar';
import { ThemeContext } from '../contexts/ThemeContext';

const CalendarPage: React.FC = () => {
  const { isDarkMode } = useContext(ThemeContext);

  return (
    <div className={`${isDarkMode ? 'bg-slate-900 text-slate-100' : 'bg-gray-100 text-slate-900'}`}>
      <TrainingCalendar isDarkMode={isDarkMode} />
    </div>
  );
};

export default CalendarPage;
