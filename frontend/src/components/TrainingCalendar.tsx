import React, { useState, useEffect } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { getTrainingSessions } from '../services/api';
import { TrainingSession } from '../types';
import TrainingSessionDialog from './TrainingSessionDialog';

interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
}

interface TrainingCalendarProps {
  isDarkMode?: boolean;
}

const localizer = momentLocalizer(moment);

const TrainingCalendar: React.FC<TrainingCalendarProps> = ({ isDarkMode }) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<{ start: Date; end: Date } | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [refreshEvents, setRefreshEvents] = useState(false);

  useEffect(() => {
    fetchTrainingSessions();
  }, [refreshEvents]);

  const fetchTrainingSessions = async () => {
    try {
      const sessions = await getTrainingSessions({ ordering: 'date,time' });
      const allEvents: CalendarEvent[] = [];
      sessions.forEach((session: TrainingSession) => {
        const eventStart = moment(session.date + ' ' + session.time).toDate();
        allEvents.push({
          id: session.id,
          title: 'Training',
          start: eventStart,
          end: moment(eventStart).add(1, 'hour').toDate(),
        });
      });
      setEvents(allEvents);
    } catch (error) {
    }
  };

  const handleSelectSlot = ({ start }: { start: Date }) => {
    setSelectedSlot({ start, end: start });
    setSelectedEvent(null);
    setShowDialog(true);
  };

  const handleSelectEvent = (event: CalendarEvent) => {
    setSelectedEvent(event);
    setSelectedSlot(null);
    setShowDialog(true);
  };

  const handleDialogClose = () => {
    setShowDialog(false);
    setSelectedEvent(null);
    setRefreshEvents((prev) => !prev);
  };

  return (
    <div className={`training-calendar p-4 ${isDarkMode ? 'bg-slate-900 text-slate-100' : 'bg-white text-black'}`}>
      <Calendar
        localizer={localizer}
        events={events}
        selectable
        onSelectSlot={handleSelectSlot}
        onSelectEvent={handleSelectEvent}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 600 }}
        views={['month', 'week', 'day']}
        className={isDarkMode ? 'pump-calendar-dark' : ''}
        eventPropGetter={(event: CalendarEvent) => ({
          style: {
            backgroundColor: isDarkMode ? '#1e293b' : '#3182ce',
            color: 'white',
          },
        })}
      />
      {showDialog && selectedSlot && !selectedEvent && (
        <TrainingSessionDialog
          show={showDialog}
          onHide={handleDialogClose}
          initialDate={selectedSlot.start}
        />
      )}
      {showDialog && selectedEvent && (
        <TrainingSessionDialog
          show={showDialog}
          onHide={handleDialogClose}
          initialEvent={selectedEvent}
        />
      )}
    </div>
  );
};

export default TrainingCalendar;
