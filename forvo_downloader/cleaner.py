import tempfile
import os
import os.path
import subprocess

import pysox


def noise_profile_path(username):
    # TODO: safety
    return './noise_profiles/{}'.format(username)


def find_noise_profile(username):
    path = noise_profile_path(username)
    if os.path.isfile(path):
        return path


def clean(path, username, noise_profile=None):
    name, ext = path.rsplit('.', 1)
    cleaned_path = '.'.join([name, 'cleaned', ext])
    new_profile = None

    remix_part = 'remix 1'
    compand_part = 'compand 0.02,0.20 5:-60,-40,-10 -5 -90 0.1'
    silence_part = 'silence 1 0.1 0.1%'

    noise_cmd = ''
    if noise_profile is None:
        noise_info = find_noise(path)
        if noise_info is not None:
            start, end, reverse = noise_info
            reverse = 'reverse' if reverse else ''
            profile_path = noise_profile_path(username)

            noise_cmd = ('sox {path} -n {remix_part} {compand_part} {reverse} '
                         'trim {start} {end} {reverse} noiseprof {out_path} &&'
                         ).format(path=path, out_path=profile_path,
                                  remix_part=remix_part, reverse=reverse,
                                  compand_part=compand_part, start=start,
                                  end=end)

            noisered_part = 'noisered {} 0.3'.format(profile_path)
            new_profile = profile_path
        else:
            noisered_part = ''
    else:
        noisered_part = 'noisered "{}" 0.3'.format(noise_profile)

    cmd = ('{noise_cmd} sox {path} {cleaned_path} {remix_part} {compand_part} '
           '{noisered_part} {silence_part} reverse {silence_part} reverse'
          ).format(noise_cmd=noise_cmd, path=path, cleaned_path=cleaned_path,
                   remix_part=remix_part, compand_part=compand_part,
                   noisered_part=noisered_part, silence_part=silence_part)
    os.system(cmd)

    return cleaned_path, new_profile


def play(path):
    """Play the sound at `path`. Requires `sox` to be installed."""

    paths = os.environ['PATH'].split(':')
    if not any([os.path.exists(os.path.join(p, 'play')) for p in paths]):
        raise RuntimeError("Can't find a `play` executable. Is sox installed "
                           "and on your PATH?")

    return subprocess.call(['play', path], stdout=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT)


def find_noise(in_path):
    in_stream = pysox.CSoxStream(in_path)

    # Try 1 second from the end first
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as end_f:
        end_path = end_f.name
        end_out = pysox.CSoxStream(end_path, 'w', in_stream.get_signal())

        end_chain = pysox.CEffectsChain(in_stream, end_out)
        end_chain.add_effect(pysox.CEffect('reverse', []))
        end_chain.add_effect(pysox.CEffect('trim', [b'0', b'1']))

        end_chain.flow_effects()
        end_out.close()

    in_stream.close()

    play(end_path)
    resp = input('Is this only noise? [Y/n] ')
    if resp.lower() in ['y', '']:
        return (0, 1, True)

    # TODO: Continue attempts?
