import React, { useEffect, useRef, useState } from 'react';
import { X, Upload, MapPin, Camera, RefreshCw, ArrowRight } from 'lucide-react';
import { useGlobeStore } from '../store/globeStore';
import { uploadPinpointImage, PinpointResultData, PinpointCandidateData } from '../lib/advancedApiClient';

export const LocationPinpointModal: React.FC = () => {
  const { isPinpointOpen, setIsPinpointOpen, setCameraPosition } = useGlobeStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [missionHint, setMissionHint] = useState<string>('Perseverance');
  const [cameraAzimuth, setCameraAzimuth] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<PinpointResultData | null>(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setIsCameraOn(false);
  };

  // Release the camera when the dialog closes or unmounts.
  useEffect(() => {
    if (!isPinpointOpen) stopCamera();
    return () => streamRef.current?.getTracks().forEach((track) => track.stop());
  }, [isPinpointOpen]);

  useEffect(() => {
    if (isCameraOn && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [isCameraOn]);

  if (!isPinpointOpen) return null;

  const acceptFile = (file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 10 MB limit.');
      return;
    }
    setSelectedFile(file);
    setErrorMsg(null);
    setResult(null);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) acceptFile(file);
  };

  const startCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setErrorMsg('This browser does not support camera access.');
      return;
    }
    try {
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      setErrorMsg(null);
      setIsCameraOn(true);
    } catch {
      setErrorMsg('Camera access was denied or no camera is available.');
    }
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        acceptFile(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }));
        stopCamera();
      },
      'image/jpeg',
      0.92,
    );
  };

  const handleRunAnalysis = async () => {
    if (!selectedFile) {
      setErrorMsg('Please select a Martian landscape image to analyze.');
      return;
    }

    try {
      setIsLoading(true);
      setErrorMsg(null);

      const formData = new FormData();
      formData.append('file', selectedFile);
      if (missionHint) formData.append('mission_hint', missionHint);
      if (cameraAzimuth) formData.append('camera_azimuth_deg', cameraAzimuth);

      const data = await uploadPinpointImage(formData);
      setResult(data);
    } catch (e: any) {
      setErrorMsg(e.message || 'Image localization analysis failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFlyToCandidate = (cand: PinpointCandidateData) => {
    setCameraPosition(cand.latitude, cand.longitude, 120000.0);
    setIsPinpointOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-950/45 p-3 sm:p-6 font-sans">
      <div className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl bg-surface-subtle text-ink shadow-panel">
        <div className="flex items-start justify-between gap-4 px-5 py-4 sm:px-7">
          <div>
            <p className="text-sm font-medium text-brand-600">Landscape match</p>
            <h2 className="mt-0.5 text-xl font-semibold tracking-tight">Where was this photo taken?</h2>
            <p className="mt-1 max-w-xl text-sm text-ink-soft">
              Add a rover or orbital picture. The matcher compares it with known terrain and returns the most likely
              places.
            </p>
          </div>
          <button
            onClick={() => setIsPinpointOpen(false)}
            className="rounded-full p-2 text-ink-muted hover:bg-white hover:text-ink"
            aria-label="Close landscape match"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="grid flex-1 grid-cols-1 gap-6 overflow-y-auto px-5 pb-5 sm:px-7 lg:grid-cols-12">
          <div className="flex flex-col gap-4 lg:col-span-5">
            {isCameraOn ? (
              <div className="flex flex-col gap-2">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="h-56 w-full rounded-2xl bg-space object-cover"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={capturePhoto}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-brand-700 px-3 py-2 text-sm font-medium text-white hover:bg-brand-800"
                  >
                    <Camera className="h-4 w-4" aria-hidden="true" />
                    Capture
                  </button>
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="rounded-lg border border-line-strong px-3 py-2 text-sm text-ink-soft hover:bg-surface-muted"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex min-h-[180px] flex-col items-center justify-center rounded-2xl border border-dashed border-line-strong bg-white px-4 py-5 text-center hover:border-brand-600"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  {previewUrl ? (
                    <div className="relative w-full">
                      <img src={previewUrl} alt="Uploaded landscape" className="h-44 w-full rounded-xl object-cover" />
                      <span className="absolute bottom-2 right-2 rounded-full bg-brand-950/75 px-2 py-1 text-[11px] text-white">
                        {selectedFile?.name}
                      </span>
                    </div>
                  ) : (
                    <>
                      <Upload className="h-6 w-6 text-brand-600" />
                      <span className="mt-3 text-sm font-medium">Choose a photo</span>
                      <span className="mt-1 text-[12px] text-ink-muted">JPEG, PNG, or WebP, up to 10 MB</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={startCamera}
                  className="flex items-center justify-center gap-2 rounded-lg border border-line-strong px-3 py-2 text-sm font-medium text-ink-soft hover:border-brand-600 hover:text-brand-700"
                >
                  <Camera className="h-4 w-4" aria-hidden="true" />
                  Use camera
                </button>
              </>
            )}

            <label className="block text-sm">
              <span className="text-ink-soft">Mission, if you know it</span>
              <select
                value={missionHint}
                onChange={(e) => setMissionHint(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line bg-white px-3 py-2 text-ink outline-none focus:border-brand-600"
              >
                <option value="Perseverance">Mars 2020 Perseverance (Jezero)</option>
                <option value="Curiosity">MSL Curiosity (Gale Crater)</option>
                <option value="Opportunity">MER Opportunity (Meridiani Planum)</option>
                <option value="Spirit">MER Spirit (Gusev Crater)</option>
                <option value="Orbital">Orbital / High Altitude Remote Sensing</option>
              </select>
            </label>

            <label className="block text-sm">
              <span className="text-ink-soft">Camera azimuth, optional</span>
              <input
                type="number"
                placeholder="135"
                value={cameraAzimuth}
                onChange={(e) => setCameraAzimuth(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line bg-white px-3 py-2 outline-none focus:border-brand-600"
              />
            </label>

            <button
              onClick={handleRunAnalysis}
              disabled={isLoading || !selectedFile}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-brand-700 py-2.5 text-sm font-medium text-white hover:bg-brand-800 disabled:opacity-50"
            >
              {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
              {isLoading ? 'Comparing the terrain' : 'Find this place'}
            </button>

            {errorMsg && <p className="rounded-xl bg-brand-50 px-3 py-2 text-sm text-brand-600">{errorMsg}</p>}
          </div>

          <div className="flex flex-col gap-3 lg:col-span-7">
            <div className="flex items-baseline justify-between">
              <h3 className="text-base font-semibold">Possible places</h3>
              {result && <span className="text-sm text-ink-muted">{result.candidates_found} checked</span>}
            </div>

            {!result && !isLoading && (
              <div className="flex flex-1 flex-col items-start justify-center rounded-2xl bg-white px-5 py-10">
                <MapPin className="h-5 w-5 text-brand-600" />
                <p className="mt-3 max-w-sm text-sm leading-relaxed text-ink-soft">
                  Matches will list a name, coordinates, elevation, and why the photo fits. You can fly the globe to any
                  of them.
                </p>
              </div>
            )}

            {result && (
              <div className="max-h-[520px] space-y-3 overflow-y-auto pr-1">
                {result.candidates.map((cand, idx) => {
                  const similarityPct = Math.round(cand.similarity_score * 100);
                  const isTop = idx === 0;
                  return (
                    <article
                      key={cand.candidate_id}
                      className={`rounded-2xl bg-white p-4 ${isTop ? 'ring-1 ring-brand-500' : ''}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h4 className="font-medium">
                            {idx + 1}. {cand.feature_name}
                            {isTop && <span className="ml-2 text-[12px] font-medium text-brand-600">Best fit</span>}
                          </h4>
                          <p className="mt-0.5 text-[13px] text-ink-muted">{cand.rover_or_mission_association}</p>
                        </div>
                        <p className="text-right">
                          <span className="text-lg font-semibold tabular-nums">{similarityPct}%</span>
                          <span className="block text-[11px] text-ink-faint">similar</span>
                        </p>
                      </div>
                      <p className="mt-3 text-[13px] tabular-nums text-ink-soft">
                        {cand.latitude.toFixed(2)}°N, {cand.longitude.toFixed(2)}°E
                        <span className="mx-1.5 text-ink-faint">·</span>
                        {cand.elevation_m.toLocaleString()} m<span className="mx-1.5 text-ink-faint">·</span>±
                        {cand.uncertainty_radius_km} km
                      </p>
                      {cand.matched_morphology.length > 0 && (
                        <p className="mt-2 text-[13px] text-ink-soft">{cand.matched_morphology.join(' · ')}</p>
                      )}
                      <p className="mt-2 text-sm leading-relaxed text-ink-soft">{cand.matching_rationale}</p>
                      <div className="mt-3 flex items-center justify-between gap-3">
                        <span className="truncate text-[12px] text-ink-faint">{cand.reference_imagery_source}</span>
                        <button
                          onClick={() => handleFlyToCandidate(cand)}
                          className="inline-flex shrink-0 items-center gap-1 rounded-full bg-ink px-3 py-1.5 text-[13px] text-white hover:bg-ink"
                        >
                          Fly there
                          <ArrowRight className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 border-t border-line px-5 py-3 text-[12px] text-ink-muted sm:px-7">
          <span>
            A research match, using edge correlation against orbital terrain. Treat the radius as the uncertainty.
          </span>
          <button onClick={() => setIsPinpointOpen(false)} className="shrink-0 font-medium text-ink hover:underline">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
