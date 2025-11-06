import { useState, useRef, type ChangeEvent } from 'react';
import { apiService } from '../../services/api';
import { useNotification } from '../../hooks/useNotification';
import { logger } from '../../utils/logger';
import type { Screenshot } from '../../types';

interface TaskScreenshotsUploadProps {
  assignmentId: number;
  screenshots: Screenshot[];
  onScreenshotsChange: (screenshots: Screenshot[]) => void;
  maxScreenshots?: number;
}

export function TaskScreenshotsUpload({
  assignmentId,
  screenshots,
  onScreenshotsChange,
  maxScreenshots = 5,
}: TaskScreenshotsUploadProps) {
  const { showSuccess, showError } = useNotification();
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const apiUrl = import.meta.env.VITE_API_URL || '';

  const toAbsoluteUrl = (value?: string) => {
    if (!value) return '';
    return value.startsWith('http') ? value : `${apiUrl}${value}`;
  };

  const buildStaticUrlFromFile = (filePath?: string) => {
    if (!filePath) return '';
    const normalized = filePath.replace(/\\/g, '/');
    const marker = '/uploads/screenshots/';
    const markerIndex = normalized.indexOf(marker);

    let relativePath = '';
    if (markerIndex >= 0) {
      relativePath = normalized.slice(markerIndex + marker.length);
    } else {
      const parts = normalized.split('/').filter(Boolean);
      const screenshotsIndex = parts.lastIndexOf('screenshots');
      if (screenshotsIndex !== -1 && screenshotsIndex + 1 < parts.length) {
        relativePath = parts.slice(screenshotsIndex + 1).join('/');
      } else {
        relativePath = parts.pop() ?? '';
      }
    }

    return relativePath ? `${apiUrl}/static/screenshots/${relativePath}` : '';
  };

  const handleFileSelect = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Check how many more screenshots we can add
    const remainingSlots = maxScreenshots - screenshots.length;
    if (remainingSlots <= 0) {
      showError(`Максимум ${maxScreenshots} скриншотов`);
      return;
    }

    // Limit files to remaining slots
    const filesToUpload = Array.from(files).slice(0, remainingSlots);
    if (filesToUpload.length < files.length) {
      showError(`Загружено ${filesToUpload.length} из ${files.length} файлов (лимит ${maxScreenshots})`);
    }

    setIsUploading(true);

    try {
      // Upload files one by one (or in parallel)
      const uploadPromises = filesToUpload.map(async (file) => {
        // Validate file type
        if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
          throw new Error(`${file.name}: Только PNG и JPG файлы`);
        }

        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
          throw new Error(`${file.name}: Файл слишком большой (макс. 10 МБ)`);
        }

        // Upload
        const result = await apiService.uploadScreenshot(assignmentId, file);
        return result;
      });

      const results = await Promise.allSettled(uploadPromises);

      // Process results
      const newScreenshots: Screenshot[] = [];
      const errors: string[] = [];

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          const screenshot = result.value;
          const absoluteUrl = toAbsoluteUrl(screenshot.url);
          const fallbackUrl = buildStaticUrlFromFile(screenshot.file_path);

          newScreenshots.push({
            id: screenshot.id,
            file_path: screenshot.file_path,
            url: absoluteUrl || fallbackUrl,
            uploaded_at: screenshot.uploaded_at,
          });
        } else {
          errors.push(result.reason.message || `Ошибка загрузки файла ${index + 1}`);
        }
      });

      // Update screenshots list
      if (newScreenshots.length > 0) {
        onScreenshotsChange([...screenshots, ...newScreenshots]);
        showSuccess(`Загружено ${newScreenshots.length} скриншотов`);
      }

      // Show errors
      if (errors.length > 0) {
        errors.forEach((error) => showError(error));
      }
    } catch (error) {
      logger.error('Upload error:', error);
      showError(error instanceof Error ? error.message : 'Ошибка загрузки');
    } finally {
      setIsUploading(false);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (screenshotId: number) => {
    try {
      await apiService.deleteScreenshot(screenshotId);
      onScreenshotsChange(screenshots.filter((s) => s.id !== screenshotId));
      showSuccess('Скриншот удален');
    } catch (error) {
      logger.error('Delete error:', error);
      showError('Не удалось удалить скриншот');
    }
  };

  const handleAddClick = () => {
    fileInputRef.current?.click();
  };

  const canAddMore = screenshots.length < maxScreenshots;

  return (
    <div className="bg-card-light dark:bg-card-dark rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
        Загрузка скриншотов
      </h2>
      <p className="text-sm text-text-muted dark:text-text-muted-dark mb-4">
        Загрузите до {maxScreenshots} скриншотов
      </p>

      {/* Screenshots Grid */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {/* Existing Screenshots */}
        {screenshots.map((screenshot) => {
          const imgUrl =
            toAbsoluteUrl(screenshot.url) || buildStaticUrlFromFile(screenshot.file_path);

          return (
            <div key={screenshot.id} className="relative aspect-square">
              <img
                src={imgUrl}
                alt="Screenshot"
                className="w-full h-full object-cover rounded-lg"
              />
              <button
                onClick={() => handleDelete(screenshot.id)}
                className="absolute -top-2 -right-2 w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
                aria-label="Удалить скриншот"
              >
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            </div>
          );
        })}

        {/* Add Button */}
        {canAddMore && (
          <button
            onClick={handleAddClick}
            disabled={isUploading}
            className={`aspect-square border-2 border-dashed rounded-lg flex flex-col items-center justify-center gap-2 transition-colors ${
              isUploading
                ? 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 cursor-not-allowed'
                : 'border-gray-300 dark:border-gray-600 hover:border-primary hover:bg-primary/5'
            }`}
          >
            {isUploading ? (
              <span className="material-symbols-outlined text-3xl text-gray-400 animate-spin">
                progress_activity
              </span>
            ) : (
              <>
                <span className="material-symbols-outlined text-3xl text-gray-400">
                  add_photo_alternate
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                  Добавить
                </span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        multiple
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Info Text */}
      <p className="text-xs text-text-muted dark:text-text-muted-dark">
        Форматы: PNG, JPG. Максимальный размер файла: 10 МБ
      </p>
    </div>
  );
}
