import chainer
from chainer import cuda
from chainer import gradient_check
import numpy
import pytest

from chainer_chemistry.config import MAX_ATOMIC_NUM
from chainer_chemistry.links.connection.embed_atom_id import EmbedAtomID
from chainer_chemistry.models.gwm import GWM, WarpGateUnit, SuperNodeTransmitterUnit, GraphTransmitterUnit
from chainer_chemistry.utils.permutation import permute_adj
from chainer_chemistry.utils.permutation import permute_node

atom_size = 5
hidden_dim = 4
supernode_dim = 7
batch_size = 2
num_edge_type = 2


@pytest.fixture
def graph_warp_gate_unit():
    return WarpGateUnit(output_type='graph', hidden_dim=hidden_dim,
                        n_layers=1)


@pytest.fixture
def super_warp_gate_unit():
    return WarpGateUnit(output_type='super', hidden_dim=supernode_dim,
                        n_layers=1)

@pytest.fixture
def super_warp_gate_unit():
    return WarpGateUnit(output_type='super', hidden_dim=supernode_dim,
                        n_layers=1)

@pytest.fixture
def super_node_transmitter_unit():
    return SuperNodeTransmitterUnit(hidden_dim_super=supernode_dim,
                                    hidden_dim=hidden_dim, n_layers=1)

@pytest.fixture
def graph_transmitter_unit():
    return GraphTransmitterUnit(hidden_dim_super=supernode_dim, hidden_dim=hidden_dim,
                                n_layers=1)


@pytest.fixture
def gwm():
    return GWM(hidden_dim=hidden_dim, hidden_dim_super=supernode_dim,
               n_layers=1)


@pytest.fixture
def data():
    numpy.random.seed(0)
    atom_data = numpy.random.randint(
        0, high=MAX_ATOMIC_NUM, size=(batch_size, atom_size)
        ).astype('i')
    new_atom_data = numpy.random.randint(
        0, high=MAX_ATOMIC_NUM, size=(batch_size, atom_size)
    ).astype('i')
    y_grad = numpy.random.uniform(
        -1, 1, (batch_size, atom_size, hidden_dim)).astype('f')
    supernode = numpy.random.uniform(-1.0, 1.0, (batch_size, supernode_dim))\
        .astype('f')
    supernode_grad = numpy.random.uniform(
        -1, 1, (batch_size, supernode_dim)).astype('f')

    embed = EmbedAtomID(in_size=MAX_ATOMIC_NUM, out_size=hidden_dim)
    embed_atom_data = embed(atom_data).data
    new_embed_atom_data = embed(new_atom_data).data
    return embed_atom_data, new_embed_atom_data, supernode, y_grad,\
           supernode_grad


def test_graph_transmitter_unit_forward(graph_transmitter_unit, data):
    embed_atom_data = data[0]
    supernode = data[2]
    h_trans = graph_transmitter_unit(embed_atom_data, supernode)
    assert h_trans.array.shape == (batch_size, supernode_dim)


def test_graph_transmitter_unit_backward(graph_transmitter_unit, data):
    embed_atom_data = data[0]
    supernode = data[2]
    supernode_grad = data[4]
    gradient_check.check_backward(graph_transmitter_unit, (embed_atom_data, supernode),
                                  supernode_grad, eps=0.1, detect_nondifferentiable=True)


def test_super_node_transmitter_unit_forward(super_node_transmitter_unit, data):
    supernode = data[2]
    g_trans = super_node_transmitter_unit(supernode, atom_size)
    assert g_trans.array.shape == (batch_size, atom_size, hidden_dim)


def test_super_node_transmitter_unit_backward(super_node_transmitter_unit, data):
    supernode = data[2]
    y_grad = data[3]
    gradient_check.check_backward(lambda x: super_node_transmitter_unit(x, atom_size), supernode,
                                  y_grad, detect_nondifferentiable=True)


def test_graph_warp_gate_unit_forward(graph_warp_gate_unit, data):
    embed_atom_data = data[0]
    new_embed_atom_data = data[1]
    merged = graph_warp_gate_unit(embed_atom_data, new_embed_atom_data)
    assert merged.array.shape == (batch_size, atom_size, hidden_dim)


def test_graph_warp_gate_unit_backward(graph_warp_gate_unit, data):
    embed_atom_data = data[0]
    new_embed_atom_data = data[1]
    y_grad = data[3]
    gradient_check.check_backward(graph_warp_gate_unit,
                                  (embed_atom_data, new_embed_atom_data),
                                  y_grad, eps=0.01, detect_nondifferentiable=True)


def test_super_warp_gate_unit_forward(super_warp_gate_unit, data):
    supernode = data[2]
    merged = super_warp_gate_unit(supernode, supernode)
    assert merged.array.shape == (batch_size, supernode_dim)


def test_super_warp_gate_unit_backward(super_warp_gate_unit, data):
    supernode = data[2]
    supernode_grad = data[4]
    gradient_check.check_backward(super_warp_gate_unit,
                                  (supernode, supernode),
                                  supernode_grad, eps=0.01, detect_nondifferentiable=True)


def check_forward(gwm, embed_atom_data, new_embed_atom_data, supernode):
    gwm.GRU_local.reset_state()
    gwm.GRU_super.reset_state()
    h_actual, g_actual = gwm(embed_atom_data, new_embed_atom_data, supernode)
    assert h_actual.array.shape == (batch_size, atom_size, hidden_dim)
    assert g_actual.array.shape == (batch_size, supernode_dim)


def test_forward_cpu(gwm, data):
    embed_atom_data, new_embed_atom_data, supernode = data[:3]
    check_forward(gwm, embed_atom_data, new_embed_atom_data, supernode)


# @pytest.mark.gpu
# def test_forward_gpu(update, data):
#     atom_data, adj_data = cuda.to_gpu(data[0]), cuda.to_gpu(data[1])
#     update.to_gpu()
#     check_forward(update, atom_data, adj_data)
#
#
def check_backward(gwm, embed_atom_data, new_embed_atom_data, supernode,
                   y_grad, supernode_grad):
    gwm.GRU_local.reset_state()
    gwm.GRU_super.reset_state()
    gradient_check.check_backward(gwm, (embed_atom_data, new_embed_atom_data,
                                        supernode), (y_grad, supernode_grad),
                                  eps=0.1, detect_nondifferentiable=False)


def test_backward_cpu(gwm, data):
    check_backward(gwm, *data)
#
#
# @pytest.mark.gpu
# def test_backward_gpu(update, data):
#     update.to_gpu()
#     check_backward(update, *map(cuda.to_gpu, data))
#
#
# def test_forward_cpu_graph_invariant(update, data):
#     permutation_index = numpy.random.permutation(atom_size)
#     atom_data, adj_data = data[:2]
#     update.reset_state()
#     y_actual = cuda.to_cpu(update(atom_data, adj_data).data)
#
#     permute_atom_data = permute_node(atom_data, permutation_index, axis=1)
#     permute_adj_data = permute_adj(adj_data, permutation_index)
#     update.reset_state()
#     permute_y_actual = cuda.to_cpu(update(
#         permute_atom_data, permute_adj_data).data)
#     numpy.testing.assert_allclose(
#         permute_node(y_actual, permutation_index, axis=1),
#         permute_y_actual, rtol=1e-5, atol=1e-5)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])