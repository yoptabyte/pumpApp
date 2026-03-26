import React, { useContext, useState, useEffect } from 'react';
import { Modal, Button, Alert } from 'react-bootstrap';
import DatePicker from 'react-datepicker';
import { createTrainingSession, updateTrainingSession, deleteTrainingSession } from '../services/api';
import { TrainingSession } from '../types';
import { ThemeContext } from '../contexts/ThemeContext';
import moment from 'moment';
import 'react-datepicker/dist/react-datepicker.css';

interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
}

interface TrainingSessionDialogProps {
  show: boolean;
  onHide: () => void;
  initialDate?: Date;
  initialEvent?: CalendarEvent;
}

const TrainingSessionDialog: React.FC<TrainingSessionDialogProps> = ({ show, onHide, initialDate, initialEvent }) => {
  const { isDarkMode } = useContext(ThemeContext);
  const [date, setDate] = useState<Date | null>(initialDate || new Date());
  const [time, setTime] = useState<Date | null>(initialDate || new Date());
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    if (initialEvent) {
      setIsEditing(true);
      setDate(initialEvent.start);
      setTime(initialEvent.start);
    } else {
      setIsEditing(false);
      const defaultDate = initialDate || new Date();
      setDate(defaultDate);
      setTime(defaultDate);
    }
    setErrorMessage('');
  }, [initialDate, initialEvent, show]);

  const handleSave = async () => {
    if (date && time) {
      const selectedDateTime = moment(date).set({
        hour: moment(time).hour(),
        minute: moment(time).minute(),
        second: 0,
        millisecond: 0,
      });

      const now = moment();

      if (selectedDateTime.isBefore(now)) {
        setErrorMessage('You cannot schedule a training session in the past.');
        return;
      }

      const dateStr = selectedDateTime.format('YYYY-MM-DD');
      const timeStr = selectedDateTime.format('HH:mm:ss');
      const data: Partial<TrainingSession> = {
        date: dateStr,
        time: timeStr,
      };
      try {
        if (isEditing && initialEvent) {
          await updateTrainingSession(initialEvent.id, data);
        } else {
          await createTrainingSession(data);
        }
        onHide();
      } catch (error) {
        setErrorMessage('An error occurred while saving the training session. Please try again.');
      }
    }
  };

  const handleDelete = async () => {
    if (initialEvent) {
      try {
        await deleteTrainingSession(initialEvent.id);
        onHide();
      } catch (error) {
        setErrorMessage('An error occurred while deleting the training session. Please try again.');
      }
    }
  };

  const filterPassedTime = (time: Date) => {
    const now = moment();
    const selectedDate = date ? moment(date).startOf('day') : moment().startOf('day');
    const selectedTime = moment(time);

    if (selectedDate.isSame(now, 'day')) {
      return selectedTime.isAfter(now);
    }
    return true;
  };

  return (
    <Modal
      show={show}
      onHide={onHide}
      centered
      contentClassName={isDarkMode ? 'bg-slate-800 text-slate-100 border border-slate-700' : ''}
    >
      <Modal.Header closeButton className={isDarkMode ? 'border-slate-700 bg-slate-800 text-slate-100' : ''}>
        <Modal.Title className={isDarkMode ? 'text-slate-100' : ''}>
          {isEditing ? 'Edit Training Session' : 'Create Training Session'}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body className={isDarkMode ? 'bg-slate-800 text-slate-100' : ''}>
        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
        <div className="mb-3">
          <label className={isDarkMode ? 'text-slate-200' : ''}>Date:</label>
          <DatePicker
            selected={date}
            onChange={(selectedDate: Date | null) => {
              setDate(selectedDate);
            }}
            dateFormat="yyyy-MM-dd"
            className={`form-control ${isDarkMode ? 'bg-slate-700 text-slate-100 border-slate-600' : ''}`}
            minDate={new Date()}
            placeholderText="Select a date"
          />
        </div>
        <div className="mb-3">
          <label className={isDarkMode ? 'text-slate-200' : ''}>Time:</label>
          <DatePicker
            selected={time}
            onChange={(selectedTime: Date | null) => setTime(selectedTime)}
            showTimeSelect
            showTimeSelectOnly
            timeIntervals={15}
            timeCaption="Time"
            dateFormat="HH:mm"
            className={`form-control ${isDarkMode ? 'bg-slate-700 text-slate-100 border-slate-600' : ''}`}
            filterTime={filterPassedTime}
            placeholderText="Select time"
          />
        </div>
      </Modal.Body>
      <Modal.Footer className={isDarkMode ? 'border-slate-700 bg-slate-800' : ''}>
        {isEditing && (
          <Button variant="danger" onClick={handleDelete} className="border-0">
            Delete
          </Button>
        )}
        <Button
          variant="secondary"
          onClick={onHide}
          className={isDarkMode ? 'border-0 bg-slate-600 hover:bg-slate-500' : ''}
        >
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSave} className="border-0">
          {isEditing ? 'Save Changes' : 'Save'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default TrainingSessionDialog;
