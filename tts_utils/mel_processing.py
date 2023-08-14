import torch
import torchaudio.transforms as T
import torch.utils.data

spectrogram_basis = {}
mel_scale_basis = {}
mel_spectrogram_basis = {}


# TODO check if necessary clip_val=1e-5
def dynamic_range_compression(x, C=1, clip_val=0):
    return torch.log(torch.clamp(x, min=clip_val) * C)


def dynamic_range_decompression(x, C=1):
    return torch.exp(x) / C


def spectral_normalize(magnitudes):
    output = dynamic_range_compression(magnitudes)
    return output


def spectral_de_normalize(magnitudes):
    output = dynamic_range_decompression(magnitudes)
    return output


def wav_to_spec(y: torch.Tensor, n_fft, sample_rate, hop_length, win_length, center=False) -> torch.Tensor:
    assert torch.min(y) >= -1.0, f"min value is {torch.min(y)}"
    assert torch.max(y) <= 1.0, f"max value is {torch.max(y)}"

    global spectrogram_basis
    dtype_device = str(y.dtype) + "_" + str(y.device)
    hparams = dtype_device + "_" + str(n_fft) + "_" + str(hop_length)
    if hparams not in spectrogram_basis:
        spectrogram_basis[hparams] = T.Spectrogram(
            n_fft=n_fft,
            win_length=win_length,
            hop_length=hop_length,
            pad=(n_fft - hop_length) // 2,
            power=1,
            center=center,
        ).to(device=y.device, dtype=y.dtype)
        # TODO print(hparams)

    spec = spectrogram_basis[hparams](y)
    # spec = torch.sqrt(spec.pow(2) + 1e-6)
    return spec


def spec_to_mel(spec: torch.Tensor, n_fft, n_mels, sample_rate, f_min, f_max) -> torch.Tensor:
    global mel_scale_basis
    dtype_device = str(spec.dtype) + "_" + str(spec.device)
    hparams = dtype_device + "_" + str(n_fft) + "_" + str(n_mels) + "_" + str(f_max)
    if hparams not in mel_scale_basis:
        mel_scale_basis[hparams] = T.MelScale(n_mels=n_mels, sample_rate=sample_rate, f_min=f_min, f_max=f_max, n_stft=n_fft // 2 + 1, norm="slaney", mel_scale="slaney").to(device=spec.device, dtype=spec.dtype)
        # TODO print(hparams)

    mel = torch.matmul(mel_scale_basis[hparams].fb.T, spec)
    # mel = spectral_normalize(mel)
    return mel


def wav_to_mel(y: torch.Tensor, n_fft, num_mels, sampling_rate, hop_size, win_size, fmin, fmax, center=False) -> torch.Tensor:
    assert torch.min(y) >= -1.0, f"min value is {torch.min(y)}"
    assert torch.max(y) <= 1.0, f"max value is {torch.max(y)}"

    global mel_spectrogram_basis
    dtype_device = str(y.dtype) + "_" + str(y.device)
    hparams = dtype_device + "_" + str(n_fft) + "_" + str(num_mels) + "_" + str(hop_size) + "_" + str(fmax)
    if hparams not in mel_spectrogram_basis:
        mel_spectrogram_basis[hparams] = T.MelSpectrogram(
            sample_rate=sampling_rate,
            n_fft=n_fft,
            win_length=win_size,
            hop_length=hop_size,
            n_mels=num_mels,
            f_min=fmin,
            f_max=fmax,
            pad=(n_fft - hop_size) // 2,
            power=1,
            center=center,
            norm="slaney",
            mel_scale="slaney",
        ).to(device=y.device, dtype=y.dtype)
        # TODO print(hparams)

    mel = mel_spectrogram_basis[hparams](y)
    # mel = spectral_normalize(mel)
    return mel
