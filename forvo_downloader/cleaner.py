import tempfile
import os
import os.path
import subprocess

import pysox

def clean(path):
    name, ext = path.rsplit('.', 1)
    cleaned_path = '.'.join([name, 'cleaned', ext])

    remix_part = 'remix 1'
    compand_part = 'compand 0.02,0.20 5:-60,-40,-10 -5 -90 0.1'
    silence_part = 'silence 1 0.1 0.1%'

    noise_cmd = ''
    do_noiseprof = True
    noise_info = find_noise(path)
    if noise_info is not None:
        start, end, reverse = noise_info
        reverse = 'reverse' if reverse else ''

        noise_cmd = ('sox {path} -n {remix_part} {compand_part} {reverse} '
                     'trim {start} {end} {reverse} noiseprof |'
                     ).format(path=path, remix_part=remix_part, reverse=reverse,
                              compand_part=compand_part, start=start, end=end)
        do_noiseprof = True

    noisered_part = 'noisered - 0.3' if do_noiseprof else ''

    cmd = ('{noise_cmd} sox {path} {cleaned_path} {remix_part} {compand_part} '
           '{noisered_part} {silence_part} reverse {silence_part} reverse'
          ).format(noise_cmd=noise_cmd, path=path, cleaned_path=cleaned_path,
                   remix_part=remix_part, compand_part=compand_part,
                   noisered_part=noisered_part, silence_part=silence_part)
    os.system(cmd)

    # pron = pysox.CSoxStream(path)
    # out = pysox.CSoxStream(cleaned_path, 'w', pron.get_signal())
    # chain = pysox.CEffectsChain(pron, out)

    # chain.add_effect(pysox.CEffect('remix', [b'1']))

    # # Dynamic range compression (normalize volume)
    # chain.add_effect(pysox.CEffect('compand', [b'0.02,0.20', b'5:-60,-40,-10',
    #                                            b'-5', b'-90', b'0.1']))

    # silence_args = [b'1', b'0.1', b'0.1%']

    # # Trim silence from front
    # chain.add_effect(pysox.CEffect('silence', silence_args))

    # # Trim silence from back
    # chain.add_effect(pysox.CEffect('reverse', []))
    # chain.add_effect(pysox.CEffect('silence', silence_args))
    # chain.add_effect(pysox.CEffect('reverse', []))

    # # Go!
    # chain.flow_effects()
    # out.close()

    return cleaned_path


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
        # print('Generating noise profile.')
        # return make_noise_profile(in_stream, 0, 1, reverse=True, in_path=in_path)
    # TODO: continue attempts


# def make_noise_profile(in_path, start_time, stop_time, reverse=True):
#     with tempfile.NamedTemporaryFile(delete=False) as f:
#         path = f.name

#         # subprocess.call(['sox', in_path, '-n', ])

#         in_stream = pysox.CSoxStream(in_path)
#         chain = pysox.CEffectsChain(in_stream, pysox.CNullFile())

#         chain.add_effect(pysox.CEffect('remix', [b'1']))

#         if reverse:
#             chain.add_effect(pysox.CEffect('reverse', []))

#         chain.add_effect(pysox.CEffect('trim', [b'0', b'1']))
#         # chain.add_effect(pysox.CEffect('trim', [str(start_time),
#         #                                         str(stop_time)]))

#         if reverse:
#             chain.add_effect(pysox.CEffect('reverse', []))

#         chain.add_effect(pysox.CEffect('noiseprof', [b'here.prof']))

#         chain.flow_effects()
#         print('here %r' % type(path))
#         in_stream.close()

#     # return path
#     return b'here.prof
